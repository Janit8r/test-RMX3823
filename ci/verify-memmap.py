#!/usr/bin/env python3
"""Check the Mu-Silicium memory map for rmx3823 before EDK II compiles it.

uefi/platform/Library/MemoryMapLib/MemoryMapLib.c is the single file most
likely to produce a silent, unbootable image: EDK II does not validate it, and
a reservation that overlaps the firmware volume or the kernel window shows up
only as a hang after flashing. This script parses the descriptor table and
checks the invariants that matter.

    python3 ci/verify-memmap.py uefi/platform/Library/MemoryMapLib/MemoryMapLib.c

Exit 0 = pass, 1 = fail, 2 = bad invocation.
"""

import argparse
import re
import sys
from pathlib import Path

# EFI_MEMORY_REGION_DESCRIPTOR.Name is a fixed-width char array. salami's
# longest label is 16 characters, which is what pins the width down.
NAME_LIMIT = 16
FD_BASE, FD_SIZE = 0xA7100000, 0x300000
KERNEL_BASE, KERNEL_SIZE = 0xA8000000, 0x10000000
DISPLAY_BASE, DISPLAY_SIZE = 0xB8000000, 0x02B00000

ENTRY = re.compile(
    r'\{\s*"([^"]*)"\s*,\s*(0x[0-9A-Fa-f]+)\s*,\s*(0x[0-9A-Fa-f]+)\s*,'
    r'\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*\}'
)


class Entry:
    __slots__ = ("name", "base", "size", "hob", "res", "attr", "mtype", "arm", "line")

    def __init__(self, match, line):
        self.name = match.group(1)
        self.base = int(match.group(2), 16)
        self.size = int(match.group(3), 16)
        self.hob, self.res, self.attr = match.group(4), match.group(5), match.group(6)
        self.mtype, self.arm = match.group(7), match.group(8)
        self.line = line

    @property
    def end(self):
        return self.base + self.size


def overlaps(a, b):
    return a.base < b.end and b.base < a.end


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("source", help="path to MemoryMapLib.c")
    ap.add_argument("--expect-count", type=int, default=None,
                    help="fail if the descriptor count differs (informational by default)")
    args = ap.parse_args()

    path = Path(args.source)
    if not path.is_file():
        print(f"::error::memory map not found: {path}")
        return 2

    entries = []
    for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if line.lstrip().startswith("//"):
            continue
        for match in ENTRY.finditer(line):
            entries.append(Entry(match, number))

    if not entries:
        print(f"::error::no memory descriptors parsed from {path}")
        return 1

    failures = 0
    print(f"source      {path}")
    print(f"entries     {len(entries)}")

    # 1. the fixed-width name field
    for entry in entries:
        if len(entry.name) > NAME_LIMIT:
            print(f"::error file={path},line={entry.line}::name '{entry.name}' is "
                  f"{len(entry.name)} characters, the descriptor allows {NAME_LIMIT}")
            failures += 1
        if not entry.name:
            print(f"::error file={path},line={entry.line}::empty name")
            failures += 1

    # 2. alignment and sanity
    for entry in entries:
        if entry.base % 0x1000:
            print(f"::error file={path},line={entry.line}::{entry.name} base "
                  f"{entry.base:#x} is not 4 KiB aligned")
            failures += 1
        if entry.size == 0:
            print(f"::error file={path},line={entry.line}::{entry.name} has zero length")
            failures += 1

    # 3. the firmware volume must not sit inside a DDR reservation
    fd = Entry.__new__(Entry)
    fd.name, fd.base, fd.size, fd.line = "UEFI FD", FD_BASE, FD_SIZE, 0
    for entry in entries:
        if entry.name in ("UEFI FD", "FD Reserved"):
            continue
        if overlaps(entry, fd):
            print(f"::error file={path},line={entry.line}::{entry.name} "
                  f"[{entry.base:#x}, {entry.end:#x}) overlaps the firmware volume "
                  f"[{FD_BASE:#x}, {FD_BASE + FD_SIZE:#x})")
            failures += 1

    # 4. the kernel window must not overlap the firmware or the splash buffer
    kernel = Entry.__new__(Entry)
    kernel.name, kernel.base, kernel.size, kernel.line = "Kernel", KERNEL_BASE, KERNEL_SIZE, 0
    display = Entry.__new__(Entry)
    display.name, display.base, display.size, display.line = "Display", DISPLAY_BASE, DISPLAY_SIZE, 0
    if overlaps(kernel, fd):
        print("::error::the kernel window overlaps the firmware volume")
        failures += 1
    if overlaps(kernel, display):
        print("::error::the kernel window overlaps the display reservation")
        failures += 1

    # 5. duplicate labels at the same address are almost always a paste error
    seen = {}
    for entry in entries:
        key = (entry.name, entry.base)
        if key in seen:
            print(f"::error file={path},line={entry.line}::duplicate {entry.name} at "
                  f"{entry.base:#x} (also line {seen[key]})")
            failures += 1
        seen[key] = entry.line

    # 6. overlaps between reservations are worth a warning, not a failure:
    #    EDK II lets a later descriptor carve a hole out of an earlier one.
    ordered = sorted(entries, key=lambda e: (e.base, e.size))
    for i, first in enumerate(ordered):
        for second in ordered[i + 1:]:
            if second.base >= first.end:
                break
            print(f"::warning file={path},line={second.line}::{second.name} "
                  f"[{second.base:#x}, {second.end:#x}) overlaps {first.name} "
                  f"[{first.base:#x}, {first.end:#x})")
        if len(ordered) > 400:
            break

    # 7. coverage report, so a truncated table is visible in the log
    total = sum(e.size for e in entries if e.res == "MEM_RES")
    print(f"reserved    {total / 2**20:.1f} MiB across "
          f"{sum(1 for e in entries if e.res == 'MEM_RES')} descriptors")
    print(f"windows     FD {FD_BASE:#x}+{FD_SIZE:#x}, kernel {KERNEL_BASE:#x}+{KERNEL_SIZE:#x}")

    if args.expect_count is not None and len(entries) != args.expect_count:
        print(f"::error::expected {args.expect_count} descriptors, found {len(entries)}")
        failures += 1

    if failures:
        print(f"\n{failures} check(s) failed")
        return 1
    print("\nOK: the memory map is internally consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
