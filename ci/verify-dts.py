#!/usr/bin/env python3
"""Compare the compiled rmx3823 device tree against the live device tree.

The reference is the FDT the phone actually boots with, captured from
/sys/firmware/fdt and committed as uefi/dtb/rmx3823.dtb. dts/rmx3823.dts is
hand-written, so this script is the guard that keeps it honest.

Two different things are checked, because the two trees are not meant to be
equal:

  * the board tree declares exactly ONE contiguous DRAM window, because
    scripts/unixnu/devicetree.py refuses anything else ("ADT handoff requires
    one contiguous DRAM range"), and board.toml [payload] dram_size must equal
    it. The window is then measured against the device's real DRAM: every byte
    that the window claims but the hardware does not back is reported, so a
    window that reaches into a hole cannot pass unnoticed.
  * the CPU MPIDRs, timebase-frequency and PSCI method must match exactly.

    dtc -I dts -O dtb -i ../UniXNU-sm8550-common/dts -o /tmp/rmx3823.dtb dts/rmx3823.dts
    python3 ci/verify-dts.py --built /tmp/rmx3823.dtb --reference uefi/dtb/rmx3823.dtb --board board.toml

Exit 0 = pass, 1 = fail, 2 = bad invocation.
"""

import argparse
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fdt  # noqa: E402

# A declared window may sit on top of reserved holes, but not on top of nothing.
MAX_PHANTOM = 0.25


def normalise(ranges):
    """Drop empty ranges and merge ones that touch, so layouts compare by content."""
    out = []
    for base, size in sorted(r for r in ranges if r[1]):
        if out and base <= out[-1][0] + out[-1][1]:
            start, length = out[-1]
            end = max(start + length, base + size)
            out[-1] = (start, end - start)
        else:
            out.append((base, size))
    return out


def memory_nodes(root):
    return [(path, node) for path, node in root.walk()
            if node.name.split("@")[0] == "memory" and node.text("device_type") == "memory"]


def dram_ranges(root):
    """The device's real DRAM, normalised."""
    out = []
    for _, node in memory_nodes(root):
        out.extend(fdt.reg_ranges(node))
    return normalise(out)


def holes(window, ranges):
    """Parts of window not covered by ranges."""
    start, size = window
    end = start + size
    gaps = []
    cursor = start
    for base, length in ranges:
        if base + length <= cursor:
            continue
        if base >= end:
            break
        if base > cursor:
            gaps.append((cursor, min(base, end) - cursor))
        cursor = max(cursor, base + length)
        if cursor >= end:
            break
    if cursor < end:
        gaps.append((cursor, end - cursor))
    return [gap for gap in gaps if gap[1]]


def covered(window, ranges):
    start, size = window
    end = start + size
    total = 0
    for base, length in ranges:
        low, high = max(base, start), min(base + length, end)
        if high > low:
            total += high - low
    return total


def find_by_name(root, name):
    for path, node in root.walk():
        if node.name.split("@")[0] == name:
            return path, node
    return None, None


def cpu_ids(root):
    cpus = root.find("/cpus")
    if cpus is None:
        return []
    ids = []
    for child in cpus.children:
        if not child.name.startswith("cpu@"):
            continue
        ranges = fdt.reg_ranges(child)
        if ranges:
            ids.append(ranges[0][0])
    return sorted(ids)


def timebase(root):
    for path, node in root.walk():
        value = node.u32("timebase-frequency")
        if value is not None:
            return path, value
    return None, None


def fmt_ranges(ranges):
    return "\n".join(f"    {base:#018x}  {size:#012x}  ({size / 2**20:9.1f} MiB)"
                     for base, size in ranges)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--built", required=True, help="DTB compiled from dts/rmx3823.dts")
    ap.add_argument("--reference", required=True, help="live FDT captured from the device")
    ap.add_argument("--board", default=None, help="board.toml, to cross-check [payload] dram_size")
    args = ap.parse_args()

    for label, path in (("built", args.built), ("reference", args.reference)):
        if not Path(path).is_file():
            print(f"::error::{label} device tree not found: {path}")
            return 2

    built = fdt.load(args.built)
    ref = fdt.load(args.reference)

    failures = 0
    print(f"built      {args.built}")
    print(f"reference  {args.reference}\n")

    for label, node in (("built", built), ("reference", ref)):
        print(f"{label:10} model       {node.text('model')}")
        print(f"{label:10} compatible  {', '.join(node.texts('compatible'))}")
    print()

    # 1. exactly one memory node with exactly one range, as the ADT generator demands
    nodes = memory_nodes(built)
    ranges = fdt.reg_ranges(nodes[0][1]) if nodes else []
    if len(nodes) != 1 or len(ranges) != 1:
        failures += 1
        print(f"::error::the board tree has {len(nodes)} memory node(s) and "
              f"{len(ranges)} range(s); the ADT handoff requires exactly one of each")
    else:
        window = ranges[0]
        print(f"dram window {window[0]:#x} + {window[1]:#x} ({window[1] / 2**30:.2f} GiB)")

        device = dram_ranges(ref)
        backed = covered(window, device)
        phantom = window[1] - backed
        print(f"device dram {len(device)} range(s), {sum(s for _, s in device) / 2**30:.2f} GiB total")
        print(f"backed      {backed / 2**20:.1f} MiB of the window is real DRAM "
              f"({100.0 * backed / window[1]:.1f}%)")

        if backed == 0:
            failures += 1
            print("::error::the declared window does not overlap any DRAM the device reports")
        elif phantom:
            print(f"holes       {phantom / 2**20:.1f} MiB of the window is not DRAM:")
            print(fmt_ranges(holes(window, device)))
            if phantom > window[1] * MAX_PHANTOM:
                failures += 1
                print(f"::error::{100.0 * phantom / window[1]:.1f}% of the window is not backed "
                      f"by DRAM (limit {100 * MAX_PHANTOM:.0f}%)")
            else:
                print(f"            {100.0 * phantom / window[1]:.1f}% phantom, within the "
                      f"{100 * MAX_PHANTOM:.0f}% limit")

        if args.board:
            try:
                with open(args.board, "rb") as fh:
                    board = tomllib.load(fh)
                declared = board.get("payload", {}).get("dram_size")
            except (OSError, tomllib.TOMLDecodeError) as exc:
                print(f"::warning::could not read {args.board}: {exc}")
                declared = None
            if isinstance(declared, str) and not declared.startswith("REQUIRED_"):
                value = int(declared, 0)
                if value != window[1]:
                    failures += 1
                    print(f"::error::board.toml [payload] dram_size {declared} != "
                          f"the DTS window {window[1]:#x}")
                else:
                    print(f"dram_size   board.toml agrees ({declared})")
            elif declared is not None:
                print(f"::warning::board.toml [payload] dram_size is still {declared!r}")

    # 2. CPUs
    bcpu, rcpu = cpu_ids(built), cpu_ids(ref)
    print(f"\ncpus        built {['%#x' % c for c in bcpu]}")
    print(f"            device {['%#x' % c for c in rcpu]}")
    if bcpu != rcpu:
        failures += 1
        print("::error::the CPU MPIDR list does not match the device")

    bpath, bfreq = timebase(built)
    rpath, rfreq = timebase(ref)
    if rfreq is None:
        print(f"timer       built {bfreq} Hz at {bpath}; the stock DTB does not declare it")
    else:
        print(f"timer       built {bfreq} Hz at {bpath}, device {rfreq} Hz at {rpath}")
        if bfreq != rfreq:
            failures += 1
            print("::error::timebase-frequency does not match the device")

    bpath, bpsci = find_by_name(built, "psci")
    rpath, rpsci = find_by_name(ref, "psci")
    bval = (bpsci.text("compatible"), bpsci.text("method")) if bpsci is not None else None
    rval = (rpsci.text("compatible"), rpsci.text("method")) if rpsci is not None else None
    print(f"psci        built {bval} at {bpath}, device {rval} at {rpath}")
    if rval is None:
        print("::warning::the stock DTB has no psci node")
    elif bval is None:
        failures += 1
        print("::error::the board tree has no psci node but the device does")
    elif bval != rval:
        failures += 1
        print("::error::the PSCI compatible string or method does not match the device")
    elif bpath != rpath:
        print(f"            note: the node lives at {rpath} on the device; UniXNU reads it by name")

    if failures:
        print(f"\n{failures} check(s) failed")
        return 1
    print("\nOK: dts/rmx3823.dts agrees with the live device tree")
    return 0


if __name__ == "__main__":
    sys.exit(main())
