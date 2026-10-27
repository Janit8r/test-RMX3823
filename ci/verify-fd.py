#!/usr/bin/env python3
"""Verify a Mu-Silicium firmware volume (SILICIUM_UEFI.fd) for rmx3823.

Checks that CI actually produced a usable EDK II firmware volume rather than an
empty or truncated file:

  * an _FVH signature exists at a plausible offset and the header is sane,
  * the FV length equals the size declared in Resources/Configs/rmx3823.toml
    (0x300000 for rmx3823; BootShim maps exactly that window),
  * the FFS walk terminates cleanly and no file claims to run past the volume,
  * PE32 DXE drivers are present, including inside nested FV_IMAGE and
    GUIDED (gzip) sections, which is how OPPO-family firmware is packaged.

Zero dependencies (stdlib only). Exit 0 = pass, 1 = fail, 2 = bad invocation.

    python3 ci/verify-fd.py --fd Build/rmx3823Pkg/RELEASE_CLANGPDB/FV/SILICIUM_UEFI.fd
"""

import argparse
import gzip
import lzma
import struct
import sys
import zlib
from pathlib import Path

FVH = b"_FVH"
FFS_TYPES = {
    0x01: "RAW", 0x02: "FREEFORM", 0x03: "SECURITY_CORE", 0x04: "PEI_CORE",
    0x05: "DXE_CORE", 0x06: "PEIM", 0x07: "DRIVER", 0x08: "COMBINED_PEIM_DRIVER",
    0x09: "APPLICATION", 0x0A: "MM", 0x0B: "FIRMWARE_VOLUME_IMAGE", 0x0C: "COMBINED_MM_DXE",
    0x0D: "MM_CORE", 0x0E: "MM_STANDALONE", 0x0F: "MM_CORE_STANDALONE",
    0xF0: "PAD", 0xFF: "ERASED",
}
SECTION_PE32 = 0x10
SECTION_GUIDED = 0x02
SECTION_FV_IMAGE = 0x17
MAX_DEPTH = 4


def u16(data, off):
    return struct.unpack_from("<H", data, off)[0]


def u64(data, off):
    return struct.unpack_from("<Q", data, off)[0]


def validate_fv(data, start):
    """Return (fv_length, header_length) when a plausible FV header sits at start."""
    if start < 0 or start + 0x38 > len(data):
        return None
    if data[start + 0x28:start + 0x2C] != FVH:
        return None
    fv_len = u64(data, start + 0x20)
    hdr_len = u16(data, start + 0x30)
    if not (0x48 <= hdr_len <= 0x2000):
        return None
    if not (0x1000 <= fv_len <= 0x8000000):
        return None
    if start + fv_len > len(data):
        return None
    return fv_len, hdr_len


def find_fv(data):
    """First valid FV in a buffer, with the _FVH offset back-computed."""
    pos = 0
    while True:
        pos = data.find(FVH, pos)
        if pos < 0:
            return None
        start = pos - 0x28
        hit = validate_fv(data, start)
        if hit:
            return start, hit[0], hit[1]
        pos += 1


def edk2_lzma(blob):
    """EDK2's LzmaCompress output: 5 header bytes, then a raw LZMA1 stream.

    The header is one properties byte (lc + lp * 9 + pb * 45) and a 4-byte
    little-endian dictionary size. That is the .lzma container minus its 8-byte
    uncompressed-size field, which is why lzma.decompress() cannot read it.
    Mu-Silicium wraps FVMAIN in a GUIDED section with the LZMA GUID
    EE4E5898-3914-4259-9D6E-DC7BD79403CF, so this is the path that matters for
    a firmware volume we build ourselves.
    """
    if len(blob) < 6:
        return None
    props = blob[0]
    if props > 224:
        return None
    dict_size = int.from_bytes(blob[1:5], "little")
    if not 0x1000 <= dict_size <= 0x10000000:
        return None
    lc = props % 9
    lp = (props // 9) % 5
    pb = props // 45
    if lc + lp > 4:
        return None
    filters = [{"id": lzma.FILTER_LZMA1, "lc": lc, "lp": lp, "pb": pb, "dict_size": dict_size}]
    try:
        return lzma.LZMADecompressor(format=lzma.FORMAT_RAW, filters=filters).decompress(blob[5:])
    except (lzma.LZMAError, ValueError, EOFError):
        return None


def decompress(blob):
    """Decode a GUIDED section payload.

    The stock OPPO image uses gzip; a Mu-Silicium build uses LZMA. Accept both,
    plus the zlib/deflate and .lzma/.xz variants, and return the first result
    that actually decompresses to something.
    """
    attempts = (
        gzip.decompress,
        zlib.decompress,
        lambda b: zlib.decompress(b, -zlib.MAX_WBITS),
        lzma.decompress,
        edk2_lzma,
    )
    for attempt in attempts:
        try:
            out = attempt(blob)
        except Exception:
            continue
        if out:
            return out
    return None


def guid_str(raw):
    a, b, c = struct.unpack_from("<IHH", raw, 0)
    return f"{a:08X}-{b:04X}-{c:04X}-{raw[8:10].hex().upper()}-{raw[10:16].hex().upper()}"


class Report:
    def __init__(self):
        self.top = None            # (offset, length, header_length)
        self.files = 0             # FFS files at depth 0
        self.used = 0              # bytes of depth-0 FFS files, 8-byte aligned
        self.by_type = {}
        self.drivers = []          # (guid, size, depth)
        self.nested_fv = 0
        self.overflow = None       # (offset, declared size)
        self.sections = 0

    def add_type(self, ftype, depth):
        if depth == 0:
            name = FFS_TYPES.get(ftype, f"0x{ftype:02X}")
            self.by_type[name] = self.by_type.get(name, 0) + 1


def walk_sections(data, start, size, depth, rep):
    """Visit the sections of one FFS file; descend into FV_IMAGE and GUIDED."""
    pos = start + 24
    end = start + size
    while pos + 4 <= end:
        ssize = data[pos] | (data[pos + 1] << 8) | (data[pos + 2] << 16)
        stype = data[pos + 3]
        if stype == 0xFF or ssize < 4 or pos + ssize > end:
            break
        rep.sections += 1
        if stype == SECTION_PE32:
            # only meaningful for DXE_DRIVER files; recorded by the caller
            pass
        elif stype == SECTION_FV_IMAGE:
            blob = data[pos:pos + ssize]
            hit = find_fv(blob)
            if hit:
                rep.nested_fv += 1
                scan_fv(blob, hit[0], hit[1], depth + 1, rep)
        elif stype == SECTION_GUIDED and depth < MAX_DEPTH:
            # EFI_SECTION_GUIDED_SECTION_PROCESSING_REQUIRED: DataOffset @ +20, Attributes @ +22
            if ssize >= 24:
                data_off = u16(data, pos + 20)
                attrs = u16(data, pos + 22)
                if attrs & 0x01 and 24 <= data_off < ssize:
                    blob = decompress(data[pos + data_off:pos + ssize])
                    if blob:
                        hit = find_fv(blob)
                        if hit:
                            rep.nested_fv += 1
                            scan_fv(blob, hit[0], hit[1], depth + 1, rep)
        pos += (ssize + 3) & ~3


def scan_fv(data, fv_start, fv_len, depth, rep):
    if depth > MAX_DEPTH:
        return
    pos = fv_start + u16(data, fv_start + 0x30)
    end = fv_start + fv_len
    while pos + 24 <= end:
        guid = data[pos:pos + 16]
        ftype = data[pos + 0x12]
        attrs = data[pos + 0x13]
        size = data[pos + 0x14] | (data[pos + 0x15] << 8) | (data[pos + 0x16] << 16)
        header = 24
        if attrs & 0x01 and size == 0xFFFFFF:              # FFS_ATTRIB_LARGE_FILE
            size = u64(data, pos + 24)
            header = 32
        if ftype == 0xFF or size < header:
            break
        if pos + size > end:
            rep.overflow = (pos, size)
            break
        rep.add_type(ftype, depth)
        if depth == 0:
            rep.files += 1
            rep.used += (size + 7) & ~7
        if ftype in (0x07, 0x09, 0x0B, 0x03, 0x05):        # driver / app / FV image / SEC / DXE core
            has_pe32 = SECTION_PE32 in section_types(data, pos + header, pos + size)
            if has_pe32:
                rep.drivers.append((guid_str(guid), size, depth))
            walk_sections(data, pos, size, depth, rep)
        pos += (size + 7) & ~7


def section_types(data, start, end):
    """Top-level section types of one FFS file."""
    kinds = []
    pos = start
    while pos + 4 <= end:
        size = data[pos] | (data[pos + 1] << 8) | (data[pos + 2] << 16)
        stype = data[pos + 3]
        if stype == 0xFF or size < 4 or pos + size > end:
            break
        kinds.append(stype)
        pos += (size + 3) & ~3
    return kinds


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fd", required=True, help="path to SILICIUM_UEFI.fd")
    ap.add_argument("--expect-size", default="0x300000",
                    help="required FV length in bytes (default 0x300000)")
    ap.add_argument("--expect-base", default=None,
                    help="informational: FD base address to print (e.g. 0xA7100000)")
    ap.add_argument("--min-drivers", type=int, default=20,
                    help="fail if fewer PE32 drivers are found (default 20)")
    ap.add_argument("--list", action="store_true", help="print every driver GUID")
    args = ap.parse_args()

    path = Path(args.fd)
    if not path.is_file():
        print(f"::error::firmware volume not found: {path}")
        return 2
    data = path.read_bytes()
    expect = int(args.expect_size, 0)

    print(f"file        {path}")
    print(f"size        {len(data)} bytes (0x{len(data):X})")
    if args.expect_base:
        base = int(args.expect_base, 0)
        print(f"base        {args.expect_base}  end 0x{base + len(data):X}")

    found = find_fv(data)
    if not found:
        print("::error::no valid EDK II firmware volume (_FVH) found")
        return 1
    fv_start, fv_len, hdr_len = found
    print(f"FV          offset 0x{fv_start:X}, length 0x{fv_len:X} ({fv_len} bytes), header 0x{hdr_len:X}")

    failed = False
    if fv_len != expect:
        print(f"::error::FV length 0x{fv_len:X} != expected 0x{expect:X}")
        failed = True

    rep = Report()
    scan_fv(data, fv_start, fv_len, 0, rep)

    print(f"FFS files   {rep.files} at the top level, {rep.nested_fv} nested firmware volume(s)")
    print(f"FV used     0x{rep.used:X} ({100.0 * rep.used / fv_len:.1f}%), free 0x{fv_len - rep.used:X}")
    for name in sorted(rep.by_type, key=lambda n: (-rep.by_type[n], n)):
        print(f"  {name:<24} {rep.by_type[name]}")

    if rep.overflow:
        print(f"::error::FFS file at 0x{rep.overflow[0]:X} declares 0x{rep.overflow[1]:X} bytes, past the FV end")
        failed = True
    if rep.files == 0:
        print("::error::the volume contains no FFS files")
        failed = True
    if len(rep.drivers) < args.min_drivers:
        print(f"::error::only {len(rep.drivers)} PE32 images found, expected at least {args.min_drivers}")
        failed = True
    else:
        print(f"PE32        {len(rep.drivers)} images ({rep.sections} sections walked)")
        shown = rep.drivers if args.list else rep.drivers[:5]
        for guid, size, depth in shown:
            print(f"  {'  ' * depth}{guid}  {size:>8} bytes")
        if not args.list and len(rep.drivers) > 5:
            print(f"  ... {len(rep.drivers) - 5} more (--list for all)")

    if failed:
        return 1
    print("\nOK: firmware volume matches the rmx3823 geometry")
    return 0


if __name__ == "__main__":
    sys.exit(main())
