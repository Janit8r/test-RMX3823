# uefi — Mu-Silicium platform overlay for realme GT5 240W

This directory is **not** a standalone repository. It is an overlay that creates
`Platforms/Realme/rmx3823Pkg` inside a [Mu-Silicium](https://github.com/Project-Silicium/Mu-Silicium)
checkout, because Mu-Silicium has no SM8550 realme package.

## What upstream already provides

| Piece | Status | Where |
| --- | --- | --- |
| SM8550 SoC layer (Kailua) | exists | `Silicon/`, `KailuaPkg` included by the DSC |
| SM8550 reference platform | exists | `Platforms/Qualcomm/qrd8550Pkg` |
| SM8550 OPPO-family platform | exists | `Platforms/OnePlus/salamiPkg` (OnePlus 11) |
| SM8550 realme platform | **missing** | this overlay creates it |
| Vendor DXE binaries | exists for `salami`, `qrd8550` | `Binaries/` (submodule `Device-Binaries`) |

So the work is genuinely thin: a board memory map, a configuration map, a DSC/FDF
and a device tree. The SoC drivers (UFS, PMIC, GIC, timer, display controller)
come from the shared Kailua layer and the `Binaries` FVs.

## What is board-specific and must be measured

| File | Content | How to obtain |
| --- | --- | --- |
| `Library/MemoryMapLib/MemoryMapLib.c` | every DDR reservation + UEFI windows | `tools/analyze-dump.py` output |
| `Library/ConfigurationMapLib/ConfigurationMapLib.c` | DDR training register, core counts | mostly shared; `DRAM_CLK_PERIOD_ADDR` needs review |
| `configs/rmx3823.toml` | `[uefi_fd]` base/size, boot image header | DT gap + stock `boot.img` header |
| `dtb/rmx3823.dtb` | firmware DTB handed to UniXNU | extracted from stock `vendor_boot_a.img` |
| `Binaries/rmx3823/` | vendor DXE drivers | extracted from the device's own UEFI FVs |

The two files shipped in `platform/Library/` are **copies of salami with a
provenance header**, i.e. a hypothesis for the first boot, not RMX3823 facts.
Replace them with the analyzer's output before reporting any result.

## Usage

```sh
git clone https://github.com/Project-Silicium/Mu-Silicium.git --recursive
sh uefi/apply.sh /path/to/Mu-Silicium
```

Then build:

```sh
cd /path/to/Mu-Silicium
python3 build_uefi.py -d rmx3823 -r RELEASE
```

The firmware volume appears at
`Build/rmx3823Pkg/RELEASE_CLANGPDB/FV/SILICIUM_UEFI.fd`. Its size must equal
`[uefi_fd] size` in `configs/rmx3823.toml` and the `UEFI FD` entry in
`MemoryMapLib.c`.

## Getting the firmware DTB

The Android bootloader passes the board DT to the payload. On a header-v4 kalama
device that DT lives in `vendor_boot`, not `boot`, and it starts at the first page
boundary after the vendor ramdisk:

```sh
# after tools/01-dump-device.sh --images
python3 tools/02-extract-vendor-dtb.py dump/<date>/images/vendor_boot_a.img \
        -o uefi/dtb/rmx3823.dtb
```

The script parses `vendor_boot_img_hdr` v4 properly (`dtb_size` at `0x834`,
`dtb_addr` at `0x838`, DTB at `page_size + align(vendor_ramdisk_size, page_size)`)
and validates the FDT magic plus `totalsize`. If it reports a bad offset, add
`--scan` to search ±4 pages, then cross-check with `unpack_bootimg --boot_img`.

## Binaries

`Binaries/salami` gets you to the first boot fastest. For a correct port, extract
RMX3823's own DXE FVs into `Binaries/rmx3823/` (same layout: `ArmPkg`,
`EmbeddedPkg`, `FatPkg`, `MdeModulePkg`, `QcomPkg`, `RawFiles`) and rebuild with
`--binaries=rmx3823`. Panel, UFS and PMIC DXE drivers are the ones that actually
differ between boards.
