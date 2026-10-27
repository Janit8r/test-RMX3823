# Firmware DTB goes here

`rmx3823.dtb` is installed and is **805,135 bytes** — the device's own live FDT,
dumped from `/sys/firmware/fdt` on the running unit. `apply.sh` copies it to
`Resources/DTBs/rmx3823.dtb`.

Do not replace it with a generic kalama MTP tree or with salami's DTB. The
bootloader injects board identity into this tree (`oplusboot.prjname=23603`, the
panel name, the touch part), and UniXNU reads the initrd range from `/chosen`
inside it.

## How this file was produced

```sh
# the live tree, with the dtbo overlay already applied by ABL
adb shell "su -c 'cp /sys/firmware/fdt /sdcard/fdt.bin'"
adb pull /sdcard/fdt.bin dump/gt5/firmware.dtb
cp dump/gt5/firmware.dtb uefi/dtb/rmx3823.dtb
```

Identity of the installed tree:

| Field | Value |
| --- | --- |
| size | 805,135 bytes |
| model | `Qualcomm Technologies, Inc. Kalama MTP,zonda-B` |
| compatible | `qcom,kalama-mtp`, `qcom,kalama`, `qcom,mtp` |
| qcom,msm-id | `0x207/0x20000`, `0x207/0x10000`, `0x218/0x20000`, `0x218/0x10000` |
| qcom,board-id | `[0x00010008, 0]` |

## The two inputs that produced it

Kept alongside for reference and for re-deriving the tree if it is ever needed:

| File | Role |
| --- | --- |
| `dump/gt5/kalama-base.dtb` | 541,212 B — `Kalama SoC`, msm-id `0x207/0x10000`, board-id `[0,0]`, taken from `vendor_boot_a` entry 1 |
| `dump/gt5/zonda-B.dtbo` | 388,966 B — `Kalama MTP,zonda-B` overlay, board-id `[8,1]`, `dtbo_a` entry 0 |

Base + overlay is what ABL merges at boot. The merged result is what this
directory ships, because that is the tree the running kernel actually sees.
