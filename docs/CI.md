# CI

Three workflows do the work this repository cannot do on a Windows host: there
is no `dtc`, no Xcode, and no ELF toolchain that EDK II is happy with.

| Workflow | File | Runner | Trigger | Minutes |
| --- | --- | --- | --- | --- |
| Validate | `validate.yml` | `ubuntu-latest` | push, pull request, manual | 1–2 |
| UEFI firmware | `uefi.yml` | `ubuntu-latest` | manual, `uefi-*` tags | 25–60 |
| UniXNU build | `unixnu.yml` | `macos-26` | manual | 60–300 |

## One-time setup

### 1. Create the repository and push

```sh
cd UniXNU-rmx3823
git init -b main
git add .
git commit -m "rmx3823: device repository, Mu-Silicium overlay and CI"
git remote add origin git@github.com:<owner>/UniXNU-rmx3823.git
git push -u origin main
```

### 2. Deploy key

The key pair in `.ci/` was generated for this repository. A deploy key is
scoped to one repository, which is what makes it safer than a personal access
token.

**Public key** → repository → *Settings* → *Deploy keys* → *Add deploy key*.
Tick **Allow write access** if you want CI (or a local clone) to push.

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINqEGVC9neDsaGN6X24MEE+hgAtZFehDiHbMN9ocPHKr unixnu-rmx3823-ci
```

**Private key** → repository → *Settings* → *Secrets and variables* → *Actions*
→ *New repository secret*, name `DEPLOY_KEY`, value the contents of
`.ci/deploy_key`.

`.ci/` is outside the repository on purpose: the private key must never be
committed.

### 3. What the deploy key is and is not for

- **It is** for `git push` / `git clone` from a machine that has no personal
  access token, and for `actions/checkout` with `ssh-key:` when the repository
  is private. `unixnu.yml` uses it when `use_deploy_key` is on (the default) and
  falls back to `github.token` when the secret is absent.
- **It is not** a substitute for `UNIXNU_DEVICE_TOKEN`. Upstream's reusable
  `macos.yml` takes a `token:` input for `actions/checkout`, which wants a
  personal access token, not an SSH key. If you ever dispatch
  `UniXNU/UniXNU/.github/workflows/macos.yml` with
  `device_repository: <owner>/UniXNU-rmx3823`, add a fine-grained PAT with
  `contents: read` on this repository as the `UNIXNU_DEVICE_TOKEN` secret in the
  **UniXNU** repository. Our own `unixnu.yml` does not need it.

## Validate

Runs on every push and pull request. Two jobs:

- **Device tree** — installs `dtc`, compiles `dts/rmx3823.dts`, then runs
  `ci/verify-dts.py` against `uefi/dtb/rmx3823.dtb`. The comparison normalises
  DRAM ranges (the stock tree pads and splits them differently) and then demands
  the same bytes, the same CPU MPIDRs and the same PSCI method. This is the job
  that would have caught every hand-written DTS mistake.
- **Repository and memory map** — `ci/verify-repo.py` (every path `board.toml`
  points at must exist, the `[firmware]` dsc must have a counterpart in `uefi/`,
  the `[uefi_fd]` window must match the BootShim contract, `porting.toml` areas
  must use known statuses), `ci/verify-memmap.py` (no reservation may overlap the
  firmware volume or the kernel window, names must fit the fixed-width field,
  no duplicate descriptors), and the firmware preflight.

A red run here means a firmware build would waste an hour or produce a boot
image that hangs.

## UEFI firmware

Manual only, because it downloads about 5 GB of Mu-Silicium.

| Input | Meaning |
| --- | --- |
| `silicium_ref` | Mu-Silicium branch, tag or commit. Pin a commit once a build works. |
| `binaries` | `salami` (OnePlus 11 vendor DXE, the only SM8550 OPPO set upstream) or `rmx3823` (needs `Binaries/rmx3823`, which does not exist yet) |
| `target` | `RELEASE` or `DEBUG` |
| `clean` | wipe `Build/` first; needed after changing the DSC or FDF |

Steps: clone Mu-Silicium recursively → `sh uefi/apply.sh Mu-Silicium` → 
`python3 build_uefi.py -d rmx3823 -r RELEASE` → `ci/verify-fd.py`.

The artifact `silicium-uefi-rmx3823` carries `SILICIUM_UEFI.fd`, its `.gz` and
`-bootshim` variants, and `verify-fd.txt`. **The FV must be exactly `0x300000`
bytes**; that is the window `uefi/configs/rmx3823.toml` gives BootShim, and the
boot image is laid out around it.

### Expected first-run failures

`binaries=salami` links OnePlus 11 vendor DXE drivers against an rmx3823 memory
map. It should compile — the platform package is a copy of salamiPkg — but the
panel, UFS and charger drivers will be wrong for this board. That is the point
of stage 1: prove the toolchain and the geometry before porting drivers.

## UniXNU build

Manual only; `macos-26` minutes are ten times the price of Linux minutes.

| Input | Meaning |
| --- | --- |
| `steps` | `kernel`, or `kernel+bootimg` to also pack a boot image |
| `xcode` | Xcode on the image, default `26.6` |
| `unixnu_ref` | UniXNU branch, tag or commit |
| `fd_run_id` | run id of a successful *UEFI firmware* run; empty picks the latest |
| `ipsw_url` | overrides `board.toml`; leave empty |
| `allow_example` | patch `example = true` to `false` in the runner checkout (default on) |
| `use_deploy_key` | check the device repository out over SSH (default on) |

`kernel+bootimg` needs two things this repository does not have yet:

1. a successful *UEFI firmware* run, and
2. a payload, which needs `[payload] dram_size`, `[payload.adt] owned_memory_size`
   and `root_match_volume_uuid` filled in, plus the `UNIXNU_UNIQUE_CHIP_ID`
   secret for `unique_chip_id = "required"`.

`./unixnu bootimg` will pack a boot image with an empty ramdisk if the payload
step has not run, which is enough to test whether UEFI comes up at all.

## After a successful build

```sh
fastboot boot rmx3823-boot.img      # never `fastboot flash` on the first attempt
```

If it hangs, the partition backups and the stock `vbmeta` state matter:
`vbmeta_a` is `flags 0x3` (AVB fully disabled) on this unit, so never flash the
`vbmeta.img` from the root image set over it.

## Local equivalents

Every check the workflows run can be run by hand:

```sh
python3 ci/verify-repo.py
python3 ci/verify-memmap.py uefi/platform/Library/MemoryMapLib/MemoryMapLib.c
python3 scripts/check-rmx3823.py
dtc -I dts -O dtb -o /tmp/rmx3823.dtb dts/rmx3823.dts
python3 ci/verify-dts.py --built /tmp/rmx3823.dtb --reference uefi/dtb/rmx3823.dtb
python3 ci/verify-fd.py --fd <SILICIUM_UEFI.fd>
```

Only the `dtc` step needs a host this project does not have on Windows; the
rest run anywhere Python 3.11+ does.
