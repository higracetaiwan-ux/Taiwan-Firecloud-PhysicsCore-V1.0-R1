# Taiwan Firecloud PhysicsCore — Current Project State

> Version: **V1.0-R5.7.41.3.4.10.11.1**  
> Internal: `1.0.0-R5.7.41.3.4.10.11.1`  
> Science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`

## Current release status

- `.10.10.2 = FIELD PASS`
- `.10.11 = REGRESSION PASS / AUTHORITATIVE SOURCE BUILD READY`
- `.10.11.1 = REGRESSION PASS / SOURCE CONTRACT CORRECTED / FULL 27-SOURCE USER RETEST REQUIRED`

## 本次已確認的 authoritative source 事實

使用者本機 Yang/Bi V2 shortwave archive：

- MD5 PASS：`2fb9bbab2c2c735a869c863a680e2f70`
- 27/27 `isca.dat` 已解壓
- hollow column 實際資料夾：`hollow_column`
- HBR 真實 sample：source QA PASS；volume wavelength spread 約 1.60；六目標波段 6/6 PASS
- SBR 真實 sample：source QA PASS；volume wavelength spread 約 1.11；六目標波段 6/6 PASS

## `.10.11` 初次 full-source gate 為何 FAIL

不是 archive 損壞。

1. builder 把 `HC` 當實體 source folder；實際是 `hollow_column`。
2. builder 把跨 wavelength 的 V invariance 當 hard gate；HBR/SBR 官方資料不符合此假設。

## `.10.11.1` 定案

Authoritative key：

`habit + roughness + Dmax + wavelength`

每個 source row 使用自己的 V/A/Qext/SSA/g 計算 `k_ext`。

`effective_radius_um` 保留為 source-row-derived diagnostic / mapping metadata，不再作 authoritative six-band key。

WINDY portable contract 升為：

`FIRECLOUD_ICE_OPTICS_PORTABLE_V1_1`

並以 Dmax lookup/interpolation；不得自行把 r_eff 轉成 Dmax。

## Frozen science

以下完全不動：

- Formation = Sun → CloudBase
- Viewing = Cloud → Observer
- Twilight Glow = independent third branch
- 550/575/600/650/700/750 nm
- Canvas 0–40 / 40–100 km
- Dynamic Corridor / REZ
- Earth Shadow / Penumbra
- Production vs Shadow COT separation
- Missing != Clear != Zero

## 下一步

在使用者本機現有：

`E:\Firecloud_DATA\Yang_Ice_LUT\extracted`

直接重跑 `.10.11.1` builder，不重新下載、不重新解壓 27 GB。

驗收目標：

- source file PASS = 27/27
- spectral target PASS = 162/162
- LUT rows = 30618
- six-band Dmax groups = 5103
- `overall_status = PASS`
- `release_ready = true`
- 產出 `Firecloud-Ice-Optics-Portable-V1.1` package

即使上述 PASS，Production Ice Optics promotion 仍維持 NO；下一階段才處理 PSD / habit mixture / Dmax↔microphysics mapping。
