"""Probe the Bun standalone module graph inside the PE `.bun` section (read-only).

Usage: python -I bun_probe.py <exe>
Prints the section header bytes, the bytes preceding the trailer, and candidate
interpretations of the Offsets struct. No extraction happens here.
"""
import mmap
import struct
import sys

TRAILER = b"\n---- Bun! ----\n"


def sections(mm):
    pe = struct.unpack_from("<I", mm, 0x3C)[0]
    nsec = struct.unpack_from("<H", mm, pe + 6)[0]
    optsz = struct.unpack_from("<H", mm, pe + 20)[0]
    sec = pe + 24 + optsz
    for i in range(nsec):
        o = sec + 40 * i
        name = mm[o:o + 8].rstrip(b"\0").decode("latin1")
        vsize, vaddr, rsize, rptr = struct.unpack_from("<IIII", mm, o + 8)
        yield name, vsize, rptr, rsize


def main():
    with open(sys.argv[1], "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        bun = [s for s in sections(mm) if s[0] == ".bun"][0]
        _, vsize, rptr, rsize = bun
        print(f".bun raw_ptr={rptr} raw_size={rsize} vsize={vsize}")
        print("first 64 bytes:", mm[rptr:rptr + 64].hex(" "))
        print("u64 @0 =", struct.unpack_from("<Q", mm, rptr)[0], " u32 @0 =", struct.unpack_from("<I", mm, rptr)[0])
        t = mm.rfind(TRAILER)
        print(f"trailer at file offset {t}  (section-relative {t - rptr}); section data end by vsize = {rptr + vsize}")
        pre = mm[t - 96:t]
        print("96 bytes before trailer:")
        for i in range(0, 96, 16):
            print(f"  -{96 - i:3d}: {pre[i:i + 16].hex(' ')}")
        print("after trailer (32):", mm[t + len(TRAILER):t + len(TRAILER) + 32].hex(" "))
        print("u32 words before trailer (last 16):", struct.unpack_from("<16I", mm, t - 64))
        mm.close()


if __name__ == "__main__":
    main()
