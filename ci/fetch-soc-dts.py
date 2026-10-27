#!/usr/bin/env python3
"""Fetch the SoC device tree include that dts/rmx3823.dts pulls in.

The board DTS starts with

    /include/ "sm8550.dtsi"

but sm8550.dtsi ships in the SoC feed (UniXNU-sm8550-common), not in this
repository. A real build resolves it because board.toml sets

    [device_tree]
    include_dirs = ["soc:dts"]

which the unixnu CLI turns into `dtc -i <soc checkout>/dts`. Anything that
compiles the DTS on its own -- CI, a local sanity check -- has to reproduce
that, or dtc fails with "Couldn't open blob from 'sm8550.dtsi'".

This script reads the pin out of feeds.toml so the fetched include is always
the same revision the build would use, and refuses a response that does not
look like a device tree (a 404 page or a truncated file is still a file).

    python3 ci/fetch-soc-dts.py --out out/soc-dts/sm8550.dtsi
    dtc -I dts -O dtb -o out/rmx3823.dtb -i out/soc-dts dts/rmx3823.dts
"""

import argparse
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

# A real sm8550.dtsi declares the three A510 cores; an error page does not.
MARKERS = (b"cortex-a510", b"psci")


def fail(message):
    print(f"fetch-soc-dts: {message}", file=sys.stderr)
    return 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--feeds", default="feeds.toml", help="feeds.toml to read the pin from")
    ap.add_argument("--out", required=True, help="where to write the .dtsi")
    ap.add_argument("--file", default="dts/sm8550.dtsi", help="path inside the feed repository")
    ap.add_argument("--timeout", type=int, default=60)
    args = ap.parse_args()

    feeds = Path(args.feeds)
    if not feeds.is_file():
        return fail(f"{feeds} not found; run this from the repository root")

    sources = tomllib.load(feeds.open("rb")).get("source", [])
    soc = next((entry for entry in sources if entry.get("kind") == "soc"), None)
    if not soc:
        return fail(f"{feeds} declares no source with kind = \"soc\"")
    for key in ("git", "commit"):
        if not soc.get(key):
            return fail(f"the soc source in {feeds} has no {key}")

    url = soc["git"]
    if not url.startswith("https://github.com/"):
        return fail(f"unsupported feed URL {url!r}; expected https://github.com/<owner>/<repo>")
    slug = url[len("https://github.com/"):].removesuffix(".git").strip("/")
    raw = f"https://raw.githubusercontent.com/{slug}/{soc['commit']}/{args.file}"

    print(f"pin         {slug} @ {soc['commit'][:12]}")
    print(f"get         {raw}")
    try:
        with urllib.request.urlopen(raw, timeout=args.timeout) as response:
            data = response.read()
    except urllib.error.HTTPError as exc:
        return fail(f"HTTP {exc.code} for {raw}")
    except (urllib.error.URLError, OSError) as exc:
        return fail(f"cannot reach {raw}: {exc}")

    missing = [marker.decode() for marker in MARKERS if marker not in data]
    if missing:
        return fail(f"{raw} does not look like a device tree (missing {', '.join(missing)}); "
                    f"got {len(data)} bytes")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    print(f"wrote       {out} ({len(data)} bytes)")
    print(f"include dir {out.parent}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
