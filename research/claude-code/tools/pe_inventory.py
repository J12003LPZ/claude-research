"""Read-only PE section inventory + Bun standalone marker scan.

Usage: python -I pe_inventory.py <path-to-exe> [out.json]
Never executes or modifies the target.
"""
import hashlib
import json
import mmap
import struct
import sys

BUN_TRAILER = b"\n---- Bun! ----\n"
MARKERS = [BUN_TRAILER, b"/$bunfs/", b"B:/~BUN/", b"bun-vfs", b"sourceMappingURL=", b"__BUN"]


def main() -> None:
    path = sys.argv[1]
    out = {"path": path}
    with open(path, "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        out["size"] = len(mm)
        out["sha256"] = hashlib.sha256(mm).hexdigest()
        assert mm[:2] == b"MZ", "not an MZ image"
        pe = struct.unpack_from("<I", mm, 0x3C)[0]
        assert mm[pe:pe + 4] == b"PE\0\0", "no PE signature"
        machine, nsec, tds, _, _, optsz, chars = struct.unpack_from("<HHIIIHH", mm, pe + 4)
        opt = pe + 24
        magic = struct.unpack_from("<H", mm, opt)[0]
        out["coff"] = {
            "machine": hex(machine),
            "sections": nsec,
            "timestamp": tds,
            "characteristics": hex(chars),
            "optional_magic": hex(magic),
        }
        if magic == 0x20B:
            out["optional"] = {
                "entry_rva": hex(struct.unpack_from("<I", mm, opt + 16)[0]),
                "image_base": hex(struct.unpack_from("<Q", mm, opt + 24)[0]),
                "subsystem": struct.unpack_from("<H", mm, opt + 68)[0],
                "size_of_image": struct.unpack_from("<I", mm, opt + 56)[0],
            }
            ddir = opt + 112
            names = ["export", "import", "resource", "exception", "security", "basereloc", "debug",
                     "arch", "globalptr", "tls", "loadconfig", "boundimport", "iat", "delayimport",
                     "clr", "reserved"]
            out["data_directories"] = {
                n: {"rva": hex(r), "size": s}
                for n, (r, s) in zip(names, [struct.unpack_from("<II", mm, ddir + 8 * i) for i in range(16)])
                if s
            }
        sec = opt + optsz
        sections = []
        end_of_sections = 0
        for i in range(nsec):
            o = sec + 40 * i
            name = mm[o:o + 8].rstrip(b"\0").decode("latin1")
            vsize, vaddr, rsize, rptr = struct.unpack_from("<IIII", mm, o + 8)
            flags = struct.unpack_from("<I", mm, o + 36)[0]
            sections.append({"name": name, "vaddr": hex(vaddr), "vsize": vsize, "raw_ptr": rptr,
                             "raw_size": rsize, "flags": hex(flags)})
            end_of_sections = max(end_of_sections, rptr + rsize)
        out["sections"] = sections
        out["end_of_sections"] = end_of_sections
        out["overlay_bytes"] = len(mm) - end_of_sections
        hits = {}
        for m in MARKERS:
            offs = []
            p = mm.find(m)
            while p != -1 and len(offs) < 5:
                offs.append(p)
                p = mm.find(m, p + 1)
            cnt = 0
            p = mm.find(m)
            while p != -1:
                cnt += 1
                p = mm.find(m, p + 1)
            hits[m.decode("latin1").strip()] = {"count": cnt, "first_offsets": offs}
        out["markers"] = hits
        # which section holds each first marker offset
        def owner(off):
            for s in sections:
                if s["raw_ptr"] <= off < s["raw_ptr"] + s["raw_size"]:
                    return s["name"]
            return "overlay" if off >= end_of_sections else "headers"
        out["marker_sections"] = {k: [owner(o) for o in v["first_offsets"]] for k, v in hits.items()}
        mm.close()
    text = json.dumps(out, indent=2)
    if len(sys.argv) > 2:
        with open(sys.argv[2], "w", encoding="utf-8") as g:
            g.write(text)
    print(text)


if __name__ == "__main__":
    main()
