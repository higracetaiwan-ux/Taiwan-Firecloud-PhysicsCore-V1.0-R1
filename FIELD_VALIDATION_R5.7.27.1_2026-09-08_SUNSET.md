# R5.7.27.1 Field Validation — 2026-09-08 Sunset

## CASE

- 檔名：`Taiwan-Firecloud-PhysicsCore-V1.0-R5.7.27.1_2026-09-08_sunset_CASE.zip`
- SHA256：`5b7238963e0eb68aa950e4e5e1ddc2aee640f7242bb084556633496ef7b6e83b`
- Runtime：`WARM_PRODUCTION`
- Core analysis：698.833 秒
- CASE archive：728.589 秒
- Peak RSS：856.605 MB

## R5.7.27.1 驗收

- `PHOTOGRAPHY_DECISION_FORMATION_ANGLE_COVERAGE = PASS`
- `PHOTOGRAPHY_FORMATION_NO_GO_DOMINANCE = PASS`
- `ANALYSIS_INTEGRITY_OVERALL = PASS`
- `ARCHIVE_MEMBER::v1_photography_decision.csv = PASS`
- Photography Decision：13/13 angles，全部 `NO_GO`

角度結果：

- 0°～−4.5°：`NO_CANVAS_RED_PATH_CONFLICT`
- −5°：`NO_CANVAS_NO_DIRECT_RED_ACCESS`
- −5.5°／−6°：`NOT_FORMED_EARTH_SHADOW`

Viewing 僅在 −5.5°／−6° 有 target 診斷，保持
`DIAGNOSTIC_ONLY_FORMATION_NO_GO`，未覆寫 Formation。

## 唯一 WARN 與根因

`CAMS_AEROSOL_SPECTRAL_PAYLOAD_VALIDITY = WARN (0.153846)`：

- CAMS 09Z `SPECTRAL_COLUMN_AOD`：90.037 秒，`TIMEOUT_DEFERRED`
- CAMS 12Z `SPECTRAL_COLUMN_AOD`：41.817 秒，`OK`
- 原 CASE 只有 −5.5°／−6° 具真實 multi-wavelength column AOD
- O3、native 3D aerosol、GFS cloud microphysics 與 gas route 均完整

R5.7.28 以同一分析已取得的 12Z 真實 CAMS spectral fields，在 3 小時硬
bound 內支援缺失的 09Z spectral chain；不搬移 O3／3D aerosol／cloud／gas／
geometry，也不使用固定 Angstrom 或人工資料。

