#!/usr/bin/env python3
"""Check that this device repository is internally consistent.

Runs in CI on every push. It catches the failures that otherwise surface only
after a 40-minute EDK II build or, worse, after flashing:

  * a board.toml that points at files this repository does not ship,
  * a [firmware] dsc / config that does not match the overlay in uefi/,
  * an [uefi_fd] window that disagrees with the BootShim the boot image uses,
  * a porting.toml area with a status the tooling does not understand,
  * a feeds.toml pin that is not a full commit id.

    python3 ci/verify-repo.py            # from the repository root
    python3 ci/verify-repo.py --unixnu ../UniXNU   # also check the OS profile exists

Exit 0 = pass, 1 = fail, 2 = bad invocation.
"""

import argparse
import re
import sys
import tomllib
from pathlib import Path

STATUSES = {"planned", "implemented", "host-verified", "device-verified", "not-applicable"}
AREAS = {
    "configuration", "firmware", "cpu", "memory", "storage", "display", "input",
    "gpu", "network", "audio", "power", "packaging", "diagnostics",
}
FD_BASE, FD_SIZE = 0xA7100000, 0x300000

REQUIRED = [
    "board.toml",
    "feeds.toml",
    "porting.toml",
    "configs/rmx3823_defconfig",
    "dts/rmx3823.dts",
    "scripts/check-rmx3823.py",
    "uefi/apply.sh",
    "uefi/configs/rmx3823.toml",
    "uefi/dtb/rmx3823.dtb",
    "uefi/platform/rmx3823.dsc",
    "uefi/platform/rmx3823.fdf",
    "uefi/platform/Library/MemoryMapLib/MemoryMapLib.c",
    "uefi/platform/Library/ConfigurationMapLib/ConfigurationMapLib.c",
]


def load(path, failures):
    try:
        with open(path, "rb") as fh:
            return tomllib.load(fh)
    except FileNotFoundError:
        print(f"::error::missing {path}")
    except tomllib.TOMLDecodeError as exc:
        print(f"::error::{path} is not valid TOML: {exc}")
    failures.append(str(path))
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=".", help="repository root (default: .)")
    ap.add_argument("--unixnu", default=None, help="UniXNU checkout, to verify the OS profile")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not (root / "board.toml").is_file():
        print(f"::error::{root} does not look like a device repository (no board.toml)")
        return 2

    failures = []
    print(f"root        {root}")

    for name in REQUIRED:
        path = root / name
        if not path.is_file():
            print(f"::error::missing {name}")
            failures.append(name)
        elif path.stat().st_size == 0:
            print(f"::error::{name} is empty")
            failures.append(name)
    print(f"files       {len(REQUIRED)} required, {len(REQUIRED) - len(failures)} present")

    board = load(root / "board.toml", failures)
    feeds = load(root / "feeds.toml", failures)
    porting = load(root / "porting.toml", failures)
    uefi = load(root / "uefi/configs/rmx3823.toml", failures)

    if board:
        if board.get("schema_version") != 2:
            print(f"::error::board.toml schema_version is {board.get('schema_version')}, expected 2")
            failures.append("board.toml")
        info = board.get("board", {})
        for key in ("name", "soc", "os_profile", "kit"):
            if not info.get(key):
                print(f"::error::board.toml [board] is missing {key}")
                failures.append("board.toml")
        if info.get("name") != "rmx3823":
            print(f"::error::board.toml [board] name is {info.get('name')!r}, expected 'rmx3823'")
            failures.append("board.toml")
        if info.get("example"):
            print("::warning::board.toml still has example = true; CI patches it for the build")

        firmware = board.get("firmware", {})
        dsc = firmware.get("dsc", "")
        if dsc and not (root / "uefi/platform" / Path(dsc).name).is_file():
            print(f"::error::[firmware] dsc {dsc!r} has no counterpart in uefi/platform/")
            failures.append("board.toml")
        if firmware.get("config") != "rmx3823":
            print(f"::error::[firmware] config is {firmware.get('config')!r}, expected 'rmx3823'")
            failures.append("board.toml")
        if "{target}" not in firmware.get("fd", ""):
            print("::error::[firmware] fd does not contain {target}")
            failures.append("board.toml")
        for script in firmware.get("preflight", []):
            if not (root / script).is_file():
                print(f"::error::[firmware] preflight script {script} does not exist")
                failures.append(script)
        print(f"firmware    config {firmware.get('config')}, dsc {Path(dsc).name}, "
              f"preflight {firmware.get('preflight')}")

        dt = board.get("device_tree", {})
        if dt.get("source") != "device:dts/rmx3823.dts":
            print(f"::warning::[device_tree] source is {dt.get('source')!r}")

        # Every /include/ in the board DTS must resolve. sm8550.dtsi ships in the
        # SoC feed rather than in this repository, so it only resolves because
        # device_tree.include_dirs points dtc at that feed. Dropping that line
        # compiles fine here and fails on the build host, so check it now.
        dts_file = root / "dts/rmx3823.dts"
        if dts_file.is_file():
            includes = re.findall(r'/include/\s+"([^"]+)"', dts_file.read_text(encoding="utf-8", errors="replace"))
            soc_feeds = [s for s in feeds.get("source", []) if s.get("kind") == "soc"] if feeds else []
            include_dirs = dt.get("include_dirs", [])
            for name in includes:
                if (root / "dts" / name).is_file():
                    continue
                provided = [
                    entry for entry in include_dirs
                    if entry.partition(":")[0] == "soc" and (Path(entry.partition(":")[2]) / name).parts
                ]
                if not provided:
                    print(f"::error::dts/rmx3823.dts includes {name!r}, which this repository does not ship, "
                          "and [device_tree] include_dirs does not point at a SoC directory that provides it")
                    failures.append("board.toml")
                elif not soc_feeds:
                    print(f"::error::[device_tree] include_dirs {provided[0]!r} relies on a soc feed, "
                          "but feeds.toml declares none")
                    failures.append("feeds.toml")
                else:
                    print(f"includes    {name} from {provided[0]} "
                          f"({soc_feeds[0].get('commit', '?')[:12]})")

        comps = board.get("components", {}).get("include", [])
        print(f"components  {len(comps)}: {', '.join(comps)}")

        if args.unixnu:
            profile = Path(args.unixnu, "profiles", "os", info.get("os_profile", ""))
            if not profile.is_dir():
                print(f"::error::OS profile {info.get('os_profile')!r} is not in {args.unixnu}/profiles/os")
                failures.append("board.toml")
            else:
                print(f"profile     {info.get('os_profile')} found")

    if uefi:
        fd = uefi.get("uefi_fd", {})
        base, size = fd.get("base"), fd.get("size")
        if base != FD_BASE:
            print(f"::error::uefi/configs/rmx3823.toml [uefi_fd] base is {base!r}, expected {FD_BASE:#x}")
            failures.append("uefi/configs/rmx3823.toml")
        if size != FD_SIZE:
            print(f"::error::uefi/configs/rmx3823.toml [uefi_fd] size is {size!r}, expected {FD_SIZE:#x}")
            failures.append("uefi/configs/rmx3823.toml")
        boot = uefi.get("boot_image", {})
        if boot.get("header_version") != 4:
            print(f"::error::[boot_image] header_version is {boot.get('header_version')!r}, "
                  "rmx3823 uses vendor_boot v4")
            failures.append("uefi/configs/rmx3823.toml")
        print(f"uefi_fd     {base:#x}+{size:#x}, boot header v{boot.get('header_version')}")

    if feeds:
        pins = []

        def collect(node, prefix=""):
            if isinstance(node, dict):
                for key, value in node.items():
                    collect(value, f"{prefix}{key}.")
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    collect(value, f"{prefix}[{index}].")
            elif isinstance(node, str) and re.fullmatch(r"[0-9a-f]{40}", node):
                pins.append(prefix.rstrip("."))

        collect(feeds)
        if not pins:
            print("::warning::feeds.toml does not pin any feed to a full commit id")
        else:
            print(f"feeds       {len(pins)} pinned commit(s)")

    if porting:
        if porting.get("schema_version") != 1:
            print(f"::error::porting.toml schema_version is {porting.get('schema_version')}, expected 1")
            failures.append("porting.toml")
        areas = porting.get("area", [])
        seen = set()
        for area in areas:
            ident, status = area.get("id"), area.get("status")
            if ident not in AREAS:
                print(f"::error::porting.toml has an unknown area id {ident!r}")
                failures.append("porting.toml")
            if status not in STATUSES:
                print(f"::error::porting.toml area {ident!r} has status {status!r}, "
                      f"expected one of {sorted(STATUSES)}")
                failures.append("porting.toml")
            if ident in seen:
                print(f"::error::porting.toml area {ident!r} appears twice")
                failures.append("porting.toml")
            seen.add(ident)
        missing = AREAS - seen
        if missing:
            print(f"::warning::porting.toml does not cover: {', '.join(sorted(missing))}")
        done = sorted(a.get("id") for a in areas if a.get("status") == "device-verified")
        print(f"porting     {len(areas)} areas, device-verified: {', '.join(done) or 'none'}")

    if failures:
        print(f"\n{len(set(failures))} check(s) failed")
        return 1
    print("\nOK: the device repository is consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
