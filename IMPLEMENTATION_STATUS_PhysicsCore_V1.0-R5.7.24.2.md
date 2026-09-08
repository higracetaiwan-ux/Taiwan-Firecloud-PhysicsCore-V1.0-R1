# Taiwan Firecloud PhysicsCore V1.0-R5.7.24.2 實作狀態

## 已完成

- R5.7.24 Runtime Reliability / Completion Guarantee
- R5.7.24 Memory Containment
- R5.7.24.1 CAMS Availability Guard
- R5.7.23.4 CASE Integrity Type Safety
- **Spectral Aerosol NOT_APPLICABLE 契約**
- **NO_TARGET_CLOUD_GEOMETRY / NO_DIRECT_SUNLIT_CANVAS_RT_REQUIRED 分離**
- **550 / 575 / 600 / 650 / 700 / 750 nm aerosol route AOD 六波段一致化**
- **native CAMS 3-D aerosol production path completeness gate**
- **real multi-wavelength AOD Sun→CloudBase fallback**
- **partial native tau 不再直接成為 public/production aerosol transmission**
- dependency evidence state 支援 `NOT_APPLICABLE`

## 本版 REAL CASE 驗證結論

以 R5.7.24.1 / 2026-09-08 sunset CASE 離線重算：

- 0°～−5°：無 Canvas target → Spectral Aerosol / Full RT = NOT_APPLICABLE
- −5.5°～−6°：Canvas 全 Earth Shadow、無 direct-sunlit target → NOT_APPLICABLE
- 原本 0% `SPECTRAL_AEROSOL_PATH=MISSING` 屬假 Missing，已修正

此 CASE 不具有 direct-sunlit Canvas，因此不能用來驗證 fallback 的 production 啟用；該路徑以專項 regression fixture 驗證。

## 專項驗證

- 六波段 route AOD 包含 575 nm
- direct-sunlit target + spectral table Missing 時仍 fail-closed
- native CAMS tau 有值但 domain incomplete 時，可切換到完整 real-AOD Sun→CloudBase fallback
- fallback 必須 path completeness / domain complete 才能標為 production complete

## 仍屬外部條件

- CAMS ADS queue / publication latency 仍可能波動
- DWD / GFS / Open-Meteo 網路可用性仍由外部服務決定
- genuine libRadtran / MYSTIC production LUT 尚未安裝

## Production LUT 狀態

`CALIBRATED DIRECTIONAL LUT NOT INSTALLED`

不得以 synthetic LUT 代替。

## Regression

**434 passed / 0 failed**（working tree）。
