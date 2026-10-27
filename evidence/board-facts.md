# RMX3823 device facts

Generated from `gt5` by `tools/analyze-dump.py`.
Everything here comes from the device itself; nothing is copied from another board.

## Identity

| Key | Value |
| --- | --- |
| DT model | `Qualcomm Technologies, Inc. Kalama MTP,zonda-B` |
| DT compatible | `qcom,kalama-mtp, qcom,kalama, qcom,mtp` |
| `oplusboot.prjname` | `23603` |
| `oplusboot.serialno` | `1d1ab949` |
| `oplusboot.verifiedbootstate` | `orange` |
| `device_info.ddr_info` | `6|8|0|6|24` |
| `msm_drm.dsi_display0` | `qcom,mdss_dsi_oplus_zonda_tianma_nt37705_1240_2772_dsc_cmd` |
| `oplus_sensor.dsi_display0` | `qcom,mdss_dsi_oplus_zonda_tianma_nt37705_1240_2772_dsc_cmd` |
| `oplus_bsp_tp_custom.dsi_display0` | `qcom,mdss_dsi_oplus_zonda_tianma_nt37705_1240_2772_dsc_cmd:synaptics-s3910` |

## DRAM

| Bank | Base | Size |
| --- | --- | --- |
| | `0x80000000` | 0.01 GiB |
| | `0x811D0000` | 1.36 GiB |
| | `0xD8140000` | 0.00 GiB |
| | `0xE1BB0000` | 0.47 GiB |
| | `0x880000000` | 0.77 GiB |
| | `0x8C0000000` | 5.00 GiB |
| | `0xA00000000` | 16.00 GiB |

Total mapped: **23.61 GiB**. Reservations: **0.65 GiB** across 43 ranges.

## Candidate free gaps for the UEFI windows

Two separate requirements, not one contiguous block:

- **FD block** (FD reserved + FD + FD reserved + info/page tables/log/stack/heaps): ~8 MiB
- **Kernel window**: 256 MiB, must be a single contiguous range

salami's layout is a useful hypothesis, not a template: FD block at `0xA7000000`
(6 MiB) and the kernel window at `0xA8000000` (256 MiB), in two adjacent gaps.

| Start | End | Size | FD block | Kernel window |
| --- | --- | --- | --- | --- |
| `0xBAB00000` | `0xD4D00000` | 418.0 MiB | yes | yes |
| `0xA760D000` | `0xB8000000` | 265.9 MiB | yes | yes |
| `0xE671D000` | `0xF3800000` | 208.9 MiB | yes | no |
| `0x82800000` | `0x8A800000` | 128.0 MiB | yes | no |
| `0xE1BB0000` | `0xE6440000` | 72.6 MiB | yes | no |
| `0xFC400000` | `0xFF800000` | 52.0 MiB | yes | no |
| `0xA4F08000` | `0xA7605000` | 39.0 MiB | yes | no |
| `0xA3280000` | `0xA4F00000` | 28.5 MiB | yes | no |

## Hardware candidates from compatible strings

### touch

| Node | compatible |
| --- | --- |
| `/soc/qcom,qupv3_1_geni_se@ac0000/i2c@a90000/goodix-berlin@5d` | `goodix,gt9916` |
| `/soc/qcom,qupv3_1_geni_se@ac0000/spi@a90000/synaptics_tcm@0` | `synaptics-s3910` |
| `/soc/qcom,qupv3_1_geni_se@ac0000/spi@a90000/synaptics_tcm_hbp@0` | `synaptics,tcm-spi-hbp` |

### storage

| Node | compatible |
| --- | --- |
| `/soc/ufsphy_mem@1d80000` | `qcom,ufs-phy-qmp-v4-kalama` |
| `/soc/ufshc@1d84000` | `qcom,ufshc` |

### wifi

| Node | compatible |
| --- | --- |
| `/soc/qcom,pcie@0x40000000` | `qcom,pcie-ep` |
| `/soc/mhi_dev@1c0b000` | `qcom,msm-mhi-dev` |
| `/soc/qcom,mhi_net_dev` | `qcom,msm-mhi-dev-net` |
| `/soc/bt-qca-converged/bt_qca6490` | `qcom,qca6490` |

### pmic

| Node | compatible |
| --- | --- |
| `/soc/qcom,spmi@c42d000` | `qcom,spmi-pmic-arb` |
| `/soc/qcom,spmi@c42d000/qcom,pm8550@1` | `qcom,spmi-pmic` |
| `/soc/qcom,spmi@c42d000/qcom,pm8550@1/pm8550-temp-alarm@a00` | `qcom,spmi-temp-alarm` |
| `/soc/qcom,spmi@c42d000/qcom,pm8550@1/pinctrl@8800` | `qcom,pm8550-gpio` |
| `/soc/qcom,spmi@c42d000/qcom,pm8550b@7` | `qcom,spmi-pmic` |
| `/soc/qcom,spmi@c42d000/qcom,pm8550b@7/pm8550b-temp-alarm@a00` | `qcom,spmi-temp-alarm` |
| `/soc/qcom,spmi@c42d000/qcom,pm8550b@7/pm8550b-temp-alarm-lite@c00` | `qcom,spmi-temp-alarm` |
| `/soc/qcom,spmi@c42d000/qcom,pm8550b@7/pinctrl@8800` | `qcom,pm8550b-gpio` |
| `/soc/qcom,spmi@c42d000/qcom,pm8550ve_f@5` | `qcom,spmi-pmic` |
| `/soc/qcom,spmi@c42d000/qcom,pm8550ve_f@5/pm8550ve-f-temp-alarm@a00` | `qcom,spmi-temp-alarm` |
| `/soc/qcom,spmi@c42d000/qcom,pm8550ve_f@5/pinctrl@8800` | `qcom,pm8550ve-gpio` |
| `/soc/qcom,spmi@c42d000/qcom,pm8550vs@2` | `qcom,spmi-pmic` |
| `/soc/qcom,spmi@c42d000/qcom,pm8550vs@2/pm8550vs-c-temp-alarm@a00` | `qcom,spmi-temp-alarm` |
| `/soc/qcom,spmi@c42d000/qcom,pm8550vs@2/pinctrl@8800` | `qcom,pm8550vs-gpio` |

### charger

| Node | compatible |
| --- | --- |
| `/soc/qcom,qupv3_2_geni_se@8c0000/i2c@880000/bq27541-battery@55` | `oplus,bq27541-battery` |
| `/soc/qcom,qupv3_2_geni_se@8c0000/i2c@884000/sc8571-master@66` | `oplus,sc8571-master` |
| `/soc/qcom,qupv3_2_geni_se@8c0000/i2c@884000/sc8571-slave@65` | `oplus,sc8571-slave` |
| `/soc/qcom,qupv3_2_geni_se@8c0000/i2c@884000/sc8571-slave-b@67` | `oplus,sc8571-slave-b` |
| `/soc/qcom,qupv3_2_geni_se@8c0000/i2c@890000/sc8517-charger@69` | `sc,sc8517-master` |

### codec

| Node | compatible |
| --- | --- |
| `/soc/qcom,qupv3_1_geni_se@ac0000/i2c@a98000/tfa98xx@34` | `nxp,tfa98xx` |
| `/soc/qcom,qupv3_1_geni_se@ac0000/i2c@a98000/tfa98xx@35` | `nxp,tfa98xx` |
| `/soc/spf_core_platform/lpass-cdc/va-macro@6D44000/va_swr_master/wcd938x-tx-slave` | `qcom,wcd938x-slave` |
| `/soc/spf_core_platform/lpass-cdc/rx-macro@6AC0000/rx_swr_master/wcd938x-rx-slave` | `qcom,wcd938x-slave` |
| `/soc/spf_core_platform/lpass-cdc/wcd938x-codec` | `qcom,wcd938x-codec` |

### gpu

| Node | compatible |
| --- | --- |
| `/soc/qcom,kgsl-3d0@3d00000` | `qcom,adreno-gpu-gen7-2-1` |
| `/soc/qcom,kgsl-3d0@3d00000` | `qcom,kgsl-3d0` |
| `/soc/kgsl-smmu@3da0000` | `qcom,adreno-smmu` |
| `/soc/qcom,kgsl-iommu@3da0000` | `qcom,kgsl-smmu-v2` |
| `/soc/qcom,kgsl-iommu@3da0000/gfx3d_user` | `qcom,smmu-kgsl-cb` |
| `/soc/qcom,kgsl-iommu@3da0000/gfx3d_lpac` | `qcom,smmu-kgsl-cb` |
| `/soc/qcom,kgsl-iommu@3da0000/gfx3d_secure` | `qcom,smmu-kgsl-cb` |
| `/soc/qcom,gmu@3d69000` | `qcom,gen7-gmu` |

## dmesg evidence

### panel

```
[32m[53612.870598] [0m[LCD][0][INFO][panel_ioctl:369] pid = 2023, cmd = PANEL_IOCTL_GET_FPS
[32m[53654.949968] [33m[TP0]touchpanel[31m: switch_usb_state_work: check usb state : 0, is_suspended: 0
[32m[53655.911622] [33m[TP0]touchpanel[31m: switch_usb_state_work: check usb state : 1, is_suspended: 0
[32m[53658.089240] [33m[TP0]touchpanel[31m: switch_usb_state_work: check usb state : 0, is_suspended: 0
[32m[53674.476791] [0m[LCD][0][INFO][panel_ioctl:369] pid = 2023, cmd = PANEL_IOCTL_GET_FPS
[32m[53730.956035] [0m[LCD][0][INFO][panel_ioctl:369] pid = 2023, cmd = PANEL_IOCTL_GET_FPS
[32m[53761.428552] [0m[LCD][0][INFO][panel_ioctl:369] pid = 2023, cmd = PANEL_IOCTL_GET_FPS
[32m[53766.428463] [0m[LCD][0][INFO][panel_ioctl:369] pid = 2023, cmd = PANEL_IOCTL_GET_FPS
```

### touch

```
[32m[53654.949968] [33m[TP0]touchpanel[31m: switch_usb_state_work: check usb state : 0, is_suspended: 0
[32m[53654.961854] [33m[TP0]synaptics-s3910[31m: OK synaptics smooth lv to 0, now reg_val:0x0
[32m[53654.970077] [33m[TP0]synaptics-s3910[31m: OK synaptics sensitive lv to 0, now reg_val:0
[32m[53655.911622] [33m[TP0]touchpanel[31m: switch_usb_state_work: check usb state : 1, is_suspended: 0
[32m[53655.922174] [33m[TP0]synaptics-s3910[31m: OK synaptics smooth lv to 0, now reg_val:0x0
[32m[53655.933451] [33m[TP0]synaptics-s3910[31m: OK synaptics sensitive lv to 0, now reg_val:0
[32m[53658.089240] [33m[TP0]touchpanel[31m: switch_usb_state_work: check usb state : 0, is_suspended: 0
[32m[53658.106823] [33m[TP0]synaptics-s3910[31m: OK synaptics smooth lv to 0, now reg_val:0x0
```

### storage

```
[32m[53599.822528] [0mGICv3:ufshcd(33):4744593
[32m[53609.294169] [0mGICv3:ufshcd(33):4744715
[32m[53618.775139] [0mGICv3:ufshcd(33):4744829
[32m[53628.239939] [0mGICv3:ufshcd(33):4744933
[32m[53637.710297] [0mGICv3:ufshcd(33):4745078
[32m[53647.182022] [0mGICv3:ufshcd(33):4745132
[32m[53656.655467] [0mGICv3:ufshcd(33):4749683
[32m[53666.126736] [0m(virq:irq_count)- GICv3:IPI(1):113420637 GICv3:arch_timer(11):85120682 GICv3:IPI(6):31850092 GICv3:apps_rsc-drv-2(20):5904802 GICv3:IPI(2):5673789 ipcc:glink-native-adsp(366):5
```

### ddr

```
[32m[54130.395381] [33mqcom-hv-haptics c42d000.qcom,spmi:qcom,pm8550b@7:qcom,hv-haptics@f000[31m: failed to kcalloc memory, try vmalloc
```

## Partitions

| Name | Block device | Size |
| --- | --- | --- |
| `ALIGN_TO_128K_1` | `/dev/block/sdd1` | 0.00 GiB |
| `ALIGN_TO_128K_2` | `/dev/block/sdf1` | 0.00 GiB |
| `DRIVER` | `/dev/block/sdf14` | 0.03 GiB |
| `abl_a` | `/dev/block/sde10` | 0.00 GiB |
| `abl_b` | `/dev/block/sde42` | 0.00 GiB |
| `aop_a` | `/dev/block/sde2` | 0.00 GiB |
| `aop_b` | `/dev/block/sde34` | 0.00 GiB |
| `aop_config_a` | `/dev/block/sde3` | 0.00 GiB |
| `aop_config_b` | `/dev/block/sde35` | 0.00 GiB |
| `apdp` | `/dev/block/sdb5` | 0.00 GiB |
| `apdp_full` | `/dev/block/sde83` | 0.00 GiB |
| `apdpb` | `/dev/block/sdc5` | 0.00 GiB |
| `bluetooth_a` | `/dev/block/sde7` | 0.01 GiB |
| `bluetooth_b` | `/dev/block/sde39` | 0.01 GiB |
| `boot_a` | `/dev/block/sde13` | 0.19 GiB |
| `boot_b` | `/dev/block/sde45` | 0.19 GiB |
| `cdt` | `/dev/block/sdd2` | 0.00 GiB |
| `connsec` | `/dev/block/sde77` | 0.00 GiB |
| `cpucp_a` | `/dev/block/sde22` | 0.00 GiB |
| `cpucp_b` | `/dev/block/sde54` | 0.00 GiB |
| `ddr` | `/dev/block/sdd3` | 0.00 GiB |
| `devcfg_a` | `/dev/block/sde14` | 0.00 GiB |
| `devcfg_b` | `/dev/block/sde46` | 0.00 GiB |
| `devinfo` | `/dev/block/sde64` | 0.00 GiB |
| `dinfo` | `/dev/block/sdd6` | 0.00 GiB |
| `dip` | `/dev/block/sde65` | 0.00 GiB |
| `dsp_a` | `/dev/block/sde11` | 0.06 GiB |
| `dsp_b` | `/dev/block/sde43` | 0.06 GiB |
| `dtbo_a` | `/dev/block/sde17` | 0.02 GiB |
| `dtbo_b` | `/dev/block/sde49` | 0.02 GiB |
| `engineering_cdt_a` | `/dev/block/sdd4` | 0.00 GiB |
| `engineering_cdt_b` | `/dev/block/sdd7` | 0.00 GiB |
| `featenabler_a` | `/dev/block/sde23` | 0.00 GiB |
| `featenabler_b` | `/dev/block/sde55` | 0.00 GiB |
| `frp` | `/dev/block/sda5` | 0.00 GiB |
| `fsc` | `/dev/block/sdf7` | 0.00 GiB |
| `fsg` | `/dev/block/sdf6` | 0.00 GiB |
| `hyp_a` | `/dev/block/sde5` | 0.01 GiB |
| `hyp_b` | `/dev/block/sde37` | 0.01 GiB |
| `imagefv_a` | `/dev/block/sde19` | 0.00 GiB |
| `imagefv_b` | `/dev/block/sde51` | 0.00 GiB |
| `init_boot_a` | `/dev/block/sde32` | 0.01 GiB |
| `init_boot_b` | `/dev/block/sde63` | 0.01 GiB |
| `keymaster_a` | `/dev/block/sde12` | 0.00 GiB |
| `keymaster_b` | `/dev/block/sde44` | 0.00 GiB |
| `keystore` | `/dev/block/sda4` | 0.00 GiB |
| `last_parti` | `/dev/block/sdd8` | 0.03 GiB |
| `limits` | `/dev/block/sde66` | 0.00 GiB |
| `limits-cdsp` | `/dev/block/sde67` | 0.00 GiB |
| `logdump` | `/dev/block/sde70` | 0.50 GiB |
| `logfs` | `/dev/block/sde69` | 0.01 GiB |
| `mdcompress` | `/dev/block/sde76` | 0.02 GiB |
| `mdm1oemnvbktmp` | `/dev/block/sdf8` | 0.00 GiB |
| `mdtp_a` | `/dev/block/sde9` | 0.03 GiB |
| `mdtp_b` | `/dev/block/sde41` | 0.03 GiB |
| `mdtpsecapp_a` | `/dev/block/sde8` | 0.00 GiB |
| `mdtpsecapp_b` | `/dev/block/sde40` | 0.00 GiB |
| `metadata` | `/dev/block/sda11` | 0.06 GiB |
| `misc` | `/dev/block/sda3` | 0.00 GiB |
| `modem_a` | `/dev/block/sde6` | 0.29 GiB |
| `modem_b` | `/dev/block/sde38` | 0.29 GiB |
| `modemst1` | `/dev/block/sdf4` | 0.00 GiB |
| `modemst2` | `/dev/block/sdf5` | 0.00 GiB |
| `multiimgoem_a` | `/dev/block/sdb4` | 0.00 GiB |
| `multiimgoem_b` | `/dev/block/sdc4` | 0.00 GiB |
| `multiimgqti_a` | `/dev/block/sdb3` | 0.00 GiB |
| `multiimgqti_b` | `/dev/block/sdc3` | 0.00 GiB |
| `ocdt` | `/dev/block/sdd5` | 0.00 GiB |
| `oplus_sec_a` | `/dev/block/sde27` | 0.01 GiB |
| `oplus_sec_b` | `/dev/block/sde58` | 0.01 GiB |
| `oplusdycnvbk` | `/dev/block/sdf2` | 0.02 GiB |
| `oplusreserve1` | `/dev/block/sdf9` | 0.01 GiB |
| `oplusreserve2` | `/dev/block/sdf10` | 0.25 GiB |
| `oplusreserve3` | `/dev/block/sdf11` | 0.06 GiB |
| `oplusreserve4` | `/dev/block/sdf12` | 0.03 GiB |
| `oplusreserve5` | `/dev/block/sdf13` | 0.06 GiB |
| `oplusstanvbk_a` | `/dev/block/sdf3` | 0.02 GiB |
| `oplusstanvbk_b` | `/dev/block/sdf15` | 0.02 GiB |
| `param` | `/dev/block/sdf16` | 0.00 GiB |
| `persist` | `/dev/block/sda2` | 0.03 GiB |
| `preisp_dt` | `/dev/block/sdf18` | 0.00 GiB |
| `preisp_dt_bk` | `/dev/block/sdf19` | 0.00 GiB |
| `preisp_otp` | `/dev/block/sdf17` | 0.00 GiB |
| `qmcs` | `/dev/block/sde25` | 0.03 GiB |
| `qupfw_a` | `/dev/block/sde15` | 0.00 GiB |
| `qupfw_b` | `/dev/block/sde47` | 0.00 GiB |
| `qweslicstore_a` | `/dev/block/sde26` | 0.00 GiB |
| `qweslicstore_b` | `/dev/block/sde57` | 0.00 GiB |
| `rawdump` | `/dev/block/sda12` | 0.25 GiB |
| `recovery_a` | `/dev/block/sde28` | 0.10 GiB |
| `recovery_b` | `/dev/block/sde59` | 0.10 GiB |
| `rtice` | `/dev/block/sde80` | 0.00 GiB |
| `rticmpdata_a` | `/dev/block/sde31` | 0.00 GiB |
| `rticmpdata_b` | `/dev/block/sde62` | 0.00 GiB |
| `sda` | `/dev/block/sda` | 949.00 GiB |
| `sdb` | `/dev/block/sdb` | 0.01 GiB |
| `sdc` | `/dev/block/sdc` | 0.01 GiB |
| `sdd` | `/dev/block/sdd` | 0.03 GiB |
| `sde` | `/dev/block/sde` | 3.77 GiB |
| `sdf` | `/dev/block/sdf` | 0.56 GiB |
| `secdata` | `/dev/block/sde73` | 0.00 GiB |
| `shrm_a` | `/dev/block/sde20` | 0.00 GiB |
| `shrm_b` | `/dev/block/sde52` | 0.00 GiB |
| `splash_a` | `/dev/block/sde29` | 0.03 GiB |
| `splash_b` | `/dev/block/sde60` | 0.03 GiB |
| `splash_odm` | `/dev/block/sda13` | 0.03 GiB |
| `spunvm` | `/dev/block/sde79` | 0.03 GiB |
| `ssd` | `/dev/block/sda1` | 0.00 GiB |
| `storsec` | `/dev/block/sde71` | 0.00 GiB |
| `super` | `/dev/block/sda6` | 13.50 GiB |
| `toolsfv` | `/dev/block/sde68` | 0.00 GiB |
| `tz_a` | `/dev/block/sde4` | 0.00 GiB |
| `tz_b` | `/dev/block/sde36` | 0.00 GiB |
| `tzsc` | `/dev/block/sde78` | 0.00 GiB |
| `uefi_a` | `/dev/block/sde1` | 0.00 GiB |
| `uefi_b` | `/dev/block/sde33` | 0.00 GiB |
| `uefisecapp_a` | `/dev/block/sde18` | 0.00 GiB |
| `uefisecapp_b` | `/dev/block/sde50` | 0.00 GiB |
| `uefivarstore` | `/dev/block/sde72` | 0.00 GiB |
| `userdata` | `/dev/block/sda14` | 935.12 GiB |
| `vbmeta_a` | `/dev/block/sde16` | 0.00 GiB |
| `vbmeta_b` | `/dev/block/sde48` | 0.00 GiB |
| `vbmeta_system_a` | `/dev/block/sda7` | 0.00 GiB |
| `vbmeta_system_b` | `/dev/block/sda8` | 0.00 GiB |
| `vbmeta_vendor_a` | `/dev/block/sda9` | 0.00 GiB |
| `vbmeta_vendor_b` | `/dev/block/sda10` | 0.00 GiB |
| `vendor_boot_a` | `/dev/block/sde24` | 0.19 GiB |
| `vendor_boot_b` | `/dev/block/sde56` | 0.19 GiB |
| `vm-bootsys_a` | `/dev/block/sde21` | 0.52 GiB |
| `vm-bootsys_b` | `/dev/block/sde53` | 0.52 GiB |
| `vm-data` | `/dev/block/sde74` | 0.03 GiB |
| `vm-persist` | `/dev/block/sde75` | 0.12 GiB |
| `xbl_a` | `/dev/block/sdb1` | 0.01 GiB |
| `xbl_b` | `/dev/block/sdc1` | 0.01 GiB |
| `xbl_config_a` | `/dev/block/sdb2` | 0.00 GiB |
| `xbl_config_b` | `/dev/block/sdc2` | 0.00 GiB |
| `xbl_ramdump_a` | `/dev/block/sde30` | 0.00 GiB |
| `xbl_ramdump_b` | `/dev/block/sde61` | 0.00 GiB |
| `xbl_sc_logs` | `/dev/block/sde82` | 0.00 GiB |
| `xbl_sc_test_mode` | `/dev/block/sde81` | 0.00 GiB |
