# Field Validation — R5.7.41.3.4.10.9.7｜2026-09-14 TWS089 日出

## 結論

`V1.0-R5.7.41.3.4.10.9.7` 本次 TWS089（蔣公碼頭）正式 CASE 完成，`.10.9.7 = FIELD PASS`。

## CASE 基本資料

- Site：TWS089 蔣公碼頭（南投縣）
- Event：2026-09-14 sunrise
- Program：`1.0.0-R5.7.41.3.4.10.9.7`
- Job：COMPLETED
- Worker elapsed：639.155 s
- `TOTAL_ANALYSIS_CORE`：602.000 s
- `TOTAL_TO_CASE_ARCHIVE`：632.435 s
- Analysis Integrity：84 PASS / 1 NOT_APPLICABLE / 0 FAIL
- CASE Integrity：38/38 PASS

## CAMS `.10.9.7` exact-source reuse

`SPECTRAL_COLUMN_AOD` 正式輸出：

- `final_status = EXACT_SOURCE_REUSE`
- `exact_source_role = AEROSOL_SCATTERING_COLUMN_PROPERTIES`
- provider elapsed = 0.0 s
- `CAMS_SPECTRAL_AOD_EXACT_REUSE_PROVENANCE = PASS`

實際 ADS provider request 為四個 fresh requests：O3 pressure-level、O3 ML137、native aerosol 532 nm、aerosol scattering column。第五列 `SPECTRAL_COLUMN_AOD` 只保留 audit handoff row，不再送 ADS request。

CAMS prefetch = 173.194 s；相較 `.10.9.6` TWS106 的 254.16 s 不能直接視為同-input benchmark，但已證明 dedicated spectral-AOD request 確實被移除。

## DWD operational hotspot

本 CASE `SECONDARY_FORECAST_NATIVE_OPTICS_PREFETCH = 158.752 s`。`dwd_icon_request_audit.csv` 顯示：

- network attempted：356
- network success：347
- network bytes：約 436,702,848 bytes（416.5 MiB）
- decoded-field runtime cache hits：1899
- persistent raw-cache hits：0
- DWD run：2026-09-13 18Z
- leads：f003 / f004

主要 byte 成本來自 P/T full-global model-level fields；QC/QI request 數亦高。這不是 Frozen Physics regression，而是 secondary provider I/O 成本。

## GFS near-field source attribution

本地點與 TWS106 不同：0–100 km source evidence 並非全零。Integrity 顯示 2160 source rows：

- exact zero：1973
- positive below threshold：0
- positive at/above threshold：7
- missing：180

正值只出現在 40–100 km extended band；0–40 km low-layer source仍為 exact zero。這證明 `.10.9.6` source-attribution 可以區分「模型 source 真零」與「確有 condensate」。

## Formation

0°→−3° 為 `PARTIAL_RED_PATH_NO_CANVAS`；−3.5°→−4.5° 出現 Canvas 但為 `UNCERTAIN_OPTICS`；−5°→−6° 為 `NOT_FORMED_EARTH_SHADOW`。本版未因 runtime optimization 改寫 Frozen Formation。

## Field 判定

- CAMS exact-source handoff：PASS
- GFS merge defragmentation：未見 regression
- Analysis / CASE Integrity：PASS
- Frozen science：無修改
- `.10.9.7 = FIELD PASS`

下一 operational target：DWD exact cache scope / HTTPS transport reuse；不得降低 model-level sampling 或跨 lead 冒充 exact evidence。
