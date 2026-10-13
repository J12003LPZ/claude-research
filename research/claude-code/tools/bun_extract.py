"""Extract the Bun standalone module graph from a PE `.bun` section (read-only on the target).

Usage: python -I bun_extract.py <exe> <manifest.json> [<extract_dir>]

Layout recovered by bun_probe.py for this build (VERIFIED against the bytes, not
assumed from Bun source):
  .bun section = u64 payload_len | payload | ...
  payload tail = Offsets{u64 byte_count, StringPointer modules, u32 entry_point_id,
                         StringPointer compile_exec_argv, u32 flags} + "\n---- Bun! ----\n"
  StringPointer = {u32 offset, u32 length}, offsets relative to payload start
  module record = 6 StringPointers (name, contents, sourcemap, bytecode, module_info,
                  bytecode_origin_path) + 4 x u8 (encoding, loader, module_format, side) = 52 bytes

The manifest lists every module with sizes and SHA-256. When <extract_dir> is given,
`contents` (and sourcemap, if present) are written there. Bytecode is hashed, never written
unless --bytecode is passed.
"""
import hashlib
import json
import mmap
import os
import re
import struct
import sys

TRAILER = b"\n---- Bun! ----\n"
REC = 52


def bun_section(mm):
    pe = struct.unpack_from("<I", mm, 0x3C)[0]
    nsec = struct.unpack_from("<H", mm, pe + 6)[0]
    optsz = struct.unpack_from("<H", mm, pe + 20)[0]
    sec = pe + 24 + optsz
    for i in range(nsec):
        o = sec + 40 * i
        if mm[o:o + 8].rstrip(b"\0") == b".bun":
            vsize, _vaddr, rsize, rptr = struct.unpack_from("<IIII", mm, o + 8)
            return rptr, vsize, rsize
    raise SystemExit("no .bun section")


def safe_rel(name: str) -> str:
    n = name.replace("\\", "/")
    n = re.sub(r"^[A-Za-z]:/", "", n)
    n = n.lstrip("/")
    parts = [re.sub(r'[<>:"|?*\x00-\x1f]', "_", p) for p in n.split("/") if p not in ("", ".", "..")]
    return "/".join(parts) or "_unnamed"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    want_bytecode = "--bytecode" in sys.argv
    exe, manifest_path = args[0], args[1]
    outdir = args[2] if len(args) > 2 else None
    with open(exe, "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        rptr, vsize, _ = bun_section(mm)
        payload_len = struct.unpack_from("<Q", mm, rptr)[0]
        base = rptr + 8
        t = mm.rfind(TRAILER)
        assert t == base + payload_len - len(TRAILER), "trailer is not at payload end"
        off = t - 32
        byte_count, m_off, m_len, entry_id, a_off, a_len, flags = struct.unpack_from("<QIIIIII", mm, off)
        assert m_len % REC == 0, f"module table length {m_len} not a multiple of {REC}"
        n = m_len // REC

        def sp(o, l):
            return mm[base + o: base + o + l]

        mods = []
        for i in range(n):
            r = base + m_off + i * REC
            (n_o, n_l, c_o, c_l, s_o, s_l, b_o, b_l, i_o, i_l, p_o, p_l,
             enc, loader, fmt, side) = struct.unpack_from("<12I4B", mm, r)
            name = sp(n_o, n_l).decode("utf-8", "replace")
            contents = sp(c_o, c_l)
            rec = {
                "index": i,
                "name": name,
                "contents": {"offset": c_o, "length": c_l,
                             "sha256": hashlib.sha256(contents).hexdigest() if c_l else None},
                "sourcemap_length": s_l,
                "bytecode": {"length": b_l,
                             "sha256": hashlib.sha256(sp(b_o, b_l)).hexdigest() if b_l else None},
                "module_info_length": i_l,
                "bytecode_origin_path": sp(p_o, p_l).decode("utf-8", "replace") if p_l else None,
                "encoding": enc, "loader": loader, "module_format": fmt, "side": side,
                "is_entry_point": i == entry_id,
            }
            if outdir:
                rel = safe_rel(name)
                dst = os.path.join(outdir, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                with open(dst, "wb") as g:
                    g.write(contents)
                rec["extracted_to"] = rel
                if s_l:
                    with open(dst + ".map.bin", "wb") as g:
                        g.write(sp(s_o, s_l))
                if want_bytecode and b_l:
                    with open(dst + ".jsc", "wb") as g:
                        g.write(sp(b_o, b_l))
            mods.append(rec)
        man = {
            "source_exe": exe,
            "source_sha256": hashlib.sha256(mm).hexdigest(),
            "bun_section": {"raw_ptr": rptr, "vsize": vsize, "payload_len": payload_len},
            "offsets": {"byte_count": byte_count, "modules_offset": m_off, "modules_length": m_len,
                        "entry_point_id": entry_id, "compile_exec_argv": sp(a_o := a_off, a_len).decode("utf-8", "replace"),
                        "flags": flags, "flags_hex": hex(flags)},
            "module_count": n,
            "record_size": REC,
            "provenance": "extracted" if outdir else "inventoried",
            "modules": mods,
        }
        mm.close()
    with open(manifest_path, "w", encoding="utf-8") as g:
        json.dump(man, g, indent=1)
    # compact console summary
    import collections
    print("modules:", n, "entry:", entry_id, mods[entry_id]["name"] if entry_id < n else None, "flags:", hex(flags))
    print("exec argv:", repr(man["offsets"]["compile_exec_argv"]))
    for key in ("loader", "encoding", "module_format", "side"):
        print(key, dict(collections.Counter(m[key] for m in mods)))
    ext = collections.Counter(os.path.splitext(m["name"])[1].lower() for m in mods)
    print("extensions:", dict(ext.most_common(20)))
    print("total contents bytes:", sum(m["contents"]["length"] for m in mods),
          "bytecode bytes:", sum(m["bytecode"]["length"] for m in mods),
          "sourcemap bytes:", sum(m["sourcemap_length"] for m in mods))
    print("largest 25:")
    for m in sorted(mods, key=lambda m: -m["contents"]["length"])[:25]:
        print(f"  {m['contents']['length']:>11}  bc={m['bytecode']['length']:>10}  L{m['loader']} F{m['module_format']}  {m['name']}")
    tops = collections.Counter("/".join(safe_rel(m["name"]).split("/")[:3]) for m in mods)
    print("top dirs:", dict(tops.most_common(30)))


if __name__ == "__main__":
    main()
