#!/usr/bin/env sh
# Create Platforms/Realme/rmx3823Pkg inside a Mu-Silicium checkout.
#
#   sh uefi/apply.sh /path/to/Mu-Silicium
#   sh uefi/apply.sh /path/to/Mu-Silicium --binaries=rmx3823
#
# The package is built by copying salamiPkg (the only SM8550 OPPO-family package
# upstream) and replacing every board-specific file. --binaries selects which
# folder under Binaries/ the Include/*.inc files point at:
#
#   salami   (default) reuse OnePlus 11 vendor DXE binaries. Fastest path to a
#            first boot; panel/UFS/power drivers may be wrong for RMX3823.
#   rmx3823  use Binaries/rmx3823, which you must populate from the device's own
#            firmware before building.
#
# Portable: works with GNU sed (Linux/CI) and BSD sed (macOS). Never uses sed -i.

set -eu

MUS=""
BINARIES="salami"
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

for arg in "$@"; do
  case "$arg" in
    --binaries=*) BINARIES="${arg#*=}" ;;
    -h|--help) sed -n '2,17p' "$0"; exit 0 ;;
    -*) echo "unknown option: $arg" >&2; exit 2 ;;
    *) MUS="$arg" ;;
  esac
done

[ -n "$MUS" ] || { echo "usage: sh apply.sh /path/to/Mu-Silicium [--binaries=rmx3823]" >&2; exit 2; }
[ -d "$MUS/Platforms/OnePlus/salamiPkg" ] || {
  echo "$MUS does not look like a Mu-Silicium checkout (missing Platforms/OnePlus/salamiPkg)" >&2
  exit 1
}

# Absolute, because the script cds into the package and then writes back into
# the checkout. With a relative path the later copies land inside the package.
MUS=$(CDPATH= cd -- "$MUS" && pwd)

# rewrite <old> -> <new> in place without relying on sed -i semantics
rewrite() {
  file=$1; old=$2; new=$3
  [ -f "$file" ] || return 0
  sed "s|$old|$new|g" "$file" > "$file.tmp.$$"
  mv "$file.tmp.$$" "$file"
}

PKG="$MUS/Platforms/Realme/rmx3823Pkg"

echo "==> copying salamiPkg -> Platforms/Realme/rmx3823Pkg"
mkdir -p "$MUS/Platforms/Realme"
rm -rf "$PKG"
cp -R "$MUS/Platforms/OnePlus/salamiPkg" "$PKG"

cd "$PKG"
mv salami.dsc rmx3823.dsc
mv salami.fdf rmx3823.fdf
if [ -f salami.dec ]; then mv salami.dec rmx3823.dec; fi

echo "==> replacing board files"
cp "$HERE/platform/rmx3823.dsc" rmx3823.dsc
cp "$HERE/platform/rmx3823.fdf" rmx3823.fdf
cp "$HERE/platform/Library/MemoryMapLib/MemoryMapLib.c" Library/MemoryMapLib/MemoryMapLib.c
cp "$HERE/platform/Library/ConfigurationMapLib/ConfigurationMapLib.c" Library/ConfigurationMapLib/ConfigurationMapLib.c

echo "==> rewriting package self-references"
for f in rmx3823.fdf Include/APRIORI.inc Include/DXE.inc Include/RAW.inc; do
  rewrite "$f" "salamiPkg" "rmx3823Pkg"
done

# DeviceBuild.py is the stuart entry point build_uefi.py drives, and it hardcodes
# the package name, the DSC path and the package search roots. Left alone, the
# build looks for Platforms/OnePlus/rmx3823Pkg/rmx3823.dsc and stops before
# compiling a single file -- which is exactly what the first CI run would have
# hit. Renaming salamiPkg first means the bare "salami" pass below cannot
# double-convert it.
if [ -f DeviceBuild.py ]; then
  echo "    DeviceBuild.py"
  rewrite DeviceBuild.py "salamiPkg" "rmx3823Pkg"
  rewrite DeviceBuild.py "salami" "rmx3823"
  # The package now lives under Platforms/Realme, which is not a search root.
  # Matches only the entry with a quote directly before it, so the
  # "Silicium-ACPI/Platforms/OnePlus" root is left untouched.
  if ! grep -q '"Platforms/Realme"' DeviceBuild.py; then
    rewrite DeviceBuild.py '"Platforms/OnePlus",' '"Platforms/Realme", "Platforms/OnePlus",'
  fi
fi

if [ "$BINARIES" = "rmx3823" ]; then
  echo "==> pointing Include/*.inc at Binaries/rmx3823"
  for f in Include/APRIORI.inc Include/DXE.inc Include/RAW.inc; do
    rewrite "$f" "Binaries/salami" "Binaries/rmx3823"
  done
  if [ ! -d "$MUS/Binaries/rmx3823" ]; then
    echo "    WARNING: $MUS/Binaries/rmx3823 does not exist yet; the build will fail until it does" >&2
  fi
else
  echo "==> keeping Binaries/salami (vendor DXE drivers from OnePlus 11)"
  echo "    replace with --binaries=rmx3823 once you have extracted the device's own FVs"
fi

echo "==> installing device config and DTB"
mkdir -p "$MUS/Resources/Configs" "$MUS/Resources/DTBs"
cp "$HERE/configs/rmx3823.toml" "$MUS/Resources/Configs/rmx3823.toml"
if [ -f "$HERE/dtb/rmx3823.dtb" ]; then
  cp "$HERE/dtb/rmx3823.dtb" "$MUS/Resources/DTBs/rmx3823.dtb"
  echo "    Resources/DTBs/rmx3823.dtb ($(wc -c < "$HERE/dtb/rmx3823.dtb" | tr -d ' ') bytes)"
else
  echo "    WARNING: uefi/dtb/rmx3823.dtb is missing." >&2
  echo "    Extract the DTB from images/vendor_boot_a.img and save it there, then re-run." >&2
fi

cat <<'EOM'

==> next
  cd <Mu-Silicium>
  python3 build_uefi.py -d rmx3823 -r RELEASE
  # output: Build/rmx3823Pkg/RELEASE_CLANGPDB/FV/SILICIUM_UEFI.fd

  # then, from the UniXNU checkout:
  ./unixnu build firmware --uefi ../Mu-Silicium
  ./unixnu bootimg  --uefi ../Mu-Silicium --dtb ../Mu-Silicium/Resources/DTBs/rmx3823.dtb

  # first attempt: boot only, never flash
  fastboot boot out/rmx3823/ipados-17.7.11-21H461/rmx3823/boot/boot.img
EOM
