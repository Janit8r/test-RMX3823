# UniXNU-rmx3823

UniXNU device repository for **realme GT5 240W (RMX3823, China)**, OPPO project
23603, Qualcomm SM8550-AB (kalama), 6.74" 1240x2772 OLED, UFS 4.0.

This port is at **stage 1**: the repository, the SoC pin, the Mu-Silicium
platform package and the board's own device tree exist, and every value in them
was measured on the unit rather than copied from a sibling board. Nothing has
been built or booted yet. `porting.toml` is the per-area record.

## Status

| Layer | State |
| --- | --- |
| Boot image (BootShim + header v4) | inputs ready, not produced yet |
| UEFI firmware (`uefi/platform`) | platform package written, not compiled |
| UniXNU.efi | reusable as-is |
| DarwinBoot | reusable as-is |
| XNU kernel | profile + SoC pin selected, no board drivers |
| iPadOS userland | not started |

## What is measured, not guessed

Everything below came from the running phone over adb (root), not from another
device's repository:

- **Identity** — `soc_id` 519 (kalama), FDT model `Kalama MTP,zonda-B`,
  `board-id [0x00010008,0]`, `prjname` 23603, `verifiedbootstate` orange,
  kernel `5.15.180-android13-8`.
- **Device tree** — `uefi/dtb/rmx3823.dtb` is `/sys/firmware/fdt`, 805,135 bytes,
  the merge of `vendor_boot_a` entry 1 (`Kalama SoC`, 541,212 bytes) and
  `dtbo_a` entry 0 (`zonda-B`, 388,966 bytes).
- **Memory** — 7 populated DRAM ranges, 23.61 GiB; 43 reservations, 0.65 GiB.
  `MemoryMapLib.c` derives its DDR entries from those reservations.
- **UEFI window** — `0xA7100000 + 0x300000` sits inside a free gap that falls
  out of the reservations, and the same addresses are what salami uses because
  both are OPPO-family kalama boards with the same reserved layout.
- **Hardware** — panel `zonda_tianma_nt37705_1240_2772_dsc_cmd`, touch
  `synaptics-s3910`, GPU `adreno-gpu-gen7-2-1`, Wi-Fi **WCN6855** (an ath11k
  part, so `Ath12kWifi` cannot be selected), PM8550 family, SC8571 + SC8517 +
  BQ27541 chargers, WCD938x + 2x TFA98xx audio, 19.2 MHz timer, PSCI 1.0 SMC.

## Layout

```
board.toml                 device definition (schema 2)
feeds.toml                 SoC feed pin
porting.toml               13-area porting record (schema 1)
configs/rmx3823_defconfig  kernel defconfig
dts/rmx3823.dts            hand-written board tree, checked against the live FDT
scripts/check-rmx3823.py   firmware preflight (board.toml [firmware] preflight)
uefi/                      Mu-Silicium overlay: apply.sh + Platforms/Realme/rmx3823Pkg
  apply.sh                 copies salamiPkg and installs every board file
  platform/                rmx3823.dsc, .fdf, MemoryMapLib, ConfigurationMapLib
  configs/rmx3823.toml     [uefi_fd] base/size + boot image header
  dtb/rmx3823.dtb          the live device tree
ci/                        checks the workflows run
.github/workflows/         validate.yml, uefi.yml, unixnu.yml
```

## Build

`uefi/` is an overlay, not a fork. It is applied to a Mu-Silicium checkout:

```sh
git clone --recursive https://github.com/Project-Silicium/Mu-Silicium
sh uefi/apply.sh Mu-Silicium                 # --binaries=rmx3823 to use Binaries/rmx3823
cd Mu-Silicium && python3 build_uefi.py -d rmx3823 -r RELEASE
```

Then, from a UniXNU checkout on macOS or Linux (Windows hosts need WSL2):

```sh
./unixnu defconfig rmx3823_defconfig -D ../UniXNU-rmx3823
./unixnu fetch
./unixnu status --json
./unixnu build kernel
./unixnu build firmware --uefi ../Mu-Silicium
./unixnu bootimg --uefi ../Mu-Silicium --dtb ../Mu-Silicium/Resources/DTBs/rmx3823.dtb
```

Build commands refuse this repository while `board.example = true`; the CI
workflows patch that flag in the runner checkout only.

## CI

Three workflows, all documented in [`docs/CI.md`](docs/CI.md):

| Workflow | Runner | What it does |
| --- | --- | --- |
| `Validate` | ubuntu | compiles the DTS, compares it with the live FDT, checks the memory map and the TOML |
| `UEFI firmware` | ubuntu | builds `SILICIUM_UEFI.fd` and asserts it is `0x300000` bytes |
| `UniXNU build` | macos-26 | runs `./unixnu build kernel` and, on request, packs the boot image |

## Reading order

- [Port a device](https://unixnu.com/porting/)
- [Device repository](https://unixnu.com/porting/device-repository)
- [UEFI firmware](https://unixnu.com/porting/uefi-firmware)
- [Driver adaptation](https://unixnu.com/porting/drivers)
- [Bring-up order](https://unixnu.com/porting/bring-up)
- [UFS](https://unixnu.com/porting/ufs), [display](https://unixnu.com/porting/display), [input](https://unixnu.com/porting/input)

`AGENTS.md` carries the repository working rules. `porting.toml` is the shared
maintainer and agent record; publish it with `board.toml` and the `unixnu` topic.
