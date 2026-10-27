#!/usr/bin/env python3
"""Preflight for the rmx3823 firmware build.

board.toml [firmware] preflight runs this before EDK II starts. It exists to
turn the two mistakes that cost the most time into one clear message: building
with a missing device tree, and building with an FD geometry that does not
match the BootShim window the boot image is laid out around.

Runs from the assembled build tree (cwd = <tree>), Python 3.11+.

Exit 0 = build, 1 = refuse, with ::error:: lines GitHub Actions understands.
"""

import sys
import tomllib
from pathlib import Path

FD_SIZE = 0x300000          # BootShim window; Resources/Configs/rmx3823.toml
FD_BASE = 0xA7100000        # first gap after the stock reservations
TREE = Path.cwd()


def error(message):
    print(f"::error::{message}")


def warn(message):
    print(f"::warning::{message}")


def load_toml(path):
    try:
        with open(path, "rb") as fh:
            return tomllib.load(fh)
    except FileNotFoundError:
        error(f"missing {path}")
    except tomllib.TOMLDecodeError as exc:
        error(f"{path} is not valid TOML: {exc}")
    return None


def check_board():
    board = load_toml(TREE / "board.toml")
    if board is None:
        return None
    firmware = board.get("firmware", {})
    if not firmware.get("dsc"):
        error("board.toml [firmware] has no dsc")
        return None
    if "{target}" not in firmware.get("fd", ""):
        warn("board.toml [firmware] fd does not use {target}; the target will be ignored")
    if board.get("board", {}).get("example"):
        warn("board.toml still has example = true; CI patches it for the duration of the run")

    payload = board.get("payload", {})
    placeholders = [key for key, value in payload.items()
                    if isinstance(value, str) and value.startswith("REQUIRED_")]
    placeholders += [f"adt.{key}" for key, value in payload.get("adt", {}).items()
                     if isinstance(value, str) and value.startswith("REQUIRED_")]
    if placeholders:
        warn("payload still has placeholder values: " + ", ".join(placeholders)
             + " (the firmware step does not read them; the payload step does)")
    return board


def check_uefi_config():
    path = TREE / "uefi/configs/rmx3823.toml"
    config = load_toml(path)
    if config is None:
        return
    fd = config.get("uefi_fd", {})
    base, size = fd.get("base"), fd.get("size")
    if base != FD_BASE:
        error(f"{path}: [uefi_fd] base is {base!r}, expected {FD_BASE:#x}")
    if size != FD_SIZE:
        error(f"{path}: [uefi_fd] size is {size!r}, expected {FD_SIZE:#x} "
              f"(BootShim maps exactly that window)")
    boot = config.get("boot_image", {})
    if boot.get("header_version") != 4:
        warn(f"{path}: [boot_image] header_version is {boot.get('header_version')!r}, "
             "rmx3823 needs 4 (vendor_boot v4 DTB section)")
    print(f"uefi config  {path}: base {base if base is None else hex(base)}, "
          f"size {size if size is None else hex(size)}, "
          f"header v{boot.get('header_version')}")


def check_dtb():
    path = TREE / "uefi/dtb/rmx3823.dtb"
    if not path.is_file():
        error(f"missing {path}: run tools/02-extract-vendor-dtb.py against vendor_boot_a.img")
        return
    data = path.read_bytes()
    if len(data) < 40 or data[:4] != b"\xd0\x0d\xfe\xed":
        error(f"{path} is not a flattened device tree (magic 0x{data[:4].hex()})")
        return
    import struct
    totalsize = struct.unpack_from(">I", data, 4)[0]
    if totalsize != len(data):
        warn(f"{path}: header totalsize {totalsize} != file size {len(data)}")
    print(f"device tree  {path}: {len(data)} bytes, totalsize {totalsize}")


def check_dts(board):
    path = TREE / "dts/rmx3823.dts"
    if not path.is_file():
        error(f"missing {path}")
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    for needle, why in (
        ('compatible = "realme,rmx3823"', "the board compatible string"),
        ("unixnu,cluster-type", "the CPU cluster tags"),
        ("splash_region", "the splash reservation bootimg rewrites"),
    ):
        if needle not in text:
            warn(f"dts/rmx3823.dts: {why} not found ({needle})")

    # The ADT generator requires exactly one memory node with exactly one range,
    # and board.toml [payload] dram_size has to equal it.
    import re
    body = re.search(r"memory@[0-9a-fA-F]+\s*\{(.*?)\n    \};", text, re.S)
    if not body:
        error("dts/rmx3823.dts has no memory@<addr> node")
    else:
        regs = re.findall(r"reg\s*=\s*<([^>]*)>", body.group(1), re.S)
        if len(regs) != 1:
            error(f"dts/rmx3823.dts declares {len(regs)} reg ranges on the memory node; "
                  "the ADT handoff requires exactly one")
        else:
            cells = [c for c in re.split(r"[\s,]+", regs[0].strip()) if c]
            if len(cells) != 4:
                error(f"the memory node reg has {len(cells)} cells, expected 4 "
                      "(root #address-cells = #size-cells = 2)")
            else:
                size = int(cells[3], 0)
                print(f"dram window  {cells[0]}/{cells[1]} + {cells[2]}/{cells[3]} "
                      f"= {size / 2**30:.2f} GiB")
                declared = (board or {}).get("payload", {}).get("dram_size")
                if isinstance(declared, str) and not declared.startswith("REQUIRED_"):
                    if int(declared, 0) != size:
                        error(f"board.toml [payload] dram_size {declared} != the DTS window {size:#x}")
    print(f"device tree  {path}: {len(text)} bytes")


def main():
    print(f"rmx3823 preflight in {TREE}")
    board = check_board()
    check_uefi_config()
    check_dtb()
    check_dts(board)
    if board is None:
        return 1
    print("preflight: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
