##
#  realme GT5 240W (RMX3823) -- Mu-Silicium platform package
#
#  Derived from Platforms/OnePlus/salamiPkg (OnePlus 11, SM8550 kalama).
#  The SoC layer lives in KailuaPkg; this package only supplies board facts.
#
#  SPDX-License-Identifier: BSD-2-Clause-Patent
##

[Defines]
  PLATFORM_NAME                  = rmx3823
  PLATFORM_GUID                  = 8C2F1B64-2E1D-4B77-9A3E-6F5D0C7A1B42
  PLATFORM_VERSION               = 0.1
  DSC_SPECIFICATION              = 0x00010005
  OUTPUT_DIRECTORY               = Build/rmx3823Pkg
  SUPPORTED_ARCHITECTURES        = AARCH64
  BUILD_TARGETS                  = RELEASE|DEBUG
  SKUID_IDENTIFIER               = DEFAULT
  FLASH_DEFINITION               = rmx3823Pkg/rmx3823.fdf
  USE_CUSTOM_DISPLAY_DRIVER      = 0

  #
  # 0 = SM8550-AB (GT5 uses SM8550-AB)
  # 1 = SM8550-AC
  #
  SOC_TYPE                       = 0

!include KailuaPkg/KailuaPkg.dsc.inc

[PcdsFixedAtBuild]
  #
  # DDR Memory
  #
  gArmTokenSpaceGuid.PcdSystemMemoryBase|0x80000000

  #
  # UEFI Stack -- must equal the "UEFI Stack" entry in MemoryMapLib.c
  #
  gArmPlatformTokenSpaceGuid.PcdCPUCoresStackBase|0xA760D000
  gArmPlatformTokenSpaceGuid.PcdCPUCorePrimaryStackSize|0x40000

  #
  # SMBIOS -- realme GT5 240W, OPPO project 23603
  #
  gSiliciumPkgTokenSpaceGuid.PcdSmbiosSystemManufacturer|"realme"
  gSiliciumPkgTokenSpaceGuid.PcdSmbiosSystemModel|"GT5 240W"
  gSiliciumPkgTokenSpaceGuid.PcdSmbiosSystemRetailModel|"rmx3823"
  gSiliciumPkgTokenSpaceGuid.PcdSmbiosSystemRetailSku|"RMX3823"
  gSiliciumPkgTokenSpaceGuid.PcdSmbiosSystemBoardModel|"23603"

  #
  # Simple Frame Buffer
  # Native panel is 1240x2772. If the first boot shows a wrong mode, drop to
  # 1080x2412 (salami's choice) before suspecting the memory map.
  #
  gSiliciumPkgTokenSpaceGuid.PcdFrameBufferWidth|1240
  gSiliciumPkgTokenSpaceGuid.PcdFrameBufferHeight|2772
  gSiliciumPkgTokenSpaceGuid.PcdFrameBufferColorDepth|32

  #
  # Platform PEI
  #
  gQcomPkgTokenSpaceGuid.PcdPlatformType|"LA"

[LibraryClasses]
  #
  # Memory Libraries
  #
  MemoryMapLib|rmx3823Pkg/Library/MemoryMapLib/MemoryMapLib.inf

  #
  # QCOM Libraries
  #
  ConfigurationMapLib|rmx3823Pkg/Library/ConfigurationMapLib/ConfigurationMapLib.inf

[Components]
  #
  # ACPI Tables
  #
  #rmx3823/AcpiTables.inf
