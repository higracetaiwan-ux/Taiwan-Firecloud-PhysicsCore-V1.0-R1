# Taiwan Firecloud PhysicsCore V1.0-R5.7.37
## 2026-09-10 Sunset CASE 實地驗證報告

### 一、正式結論

本次 R5.7.37 CASE 已完成實地驗證。

- Analysis Integrity：**61 PASS / 0 WARN / 0 FAIL**
- Case Integrity：**23 PASS / 0 WARN / 0 FAIL**
- `TWILIGHT_GLOW_OBSERVER_DEEP_RANGE_MOLECULAR_COVERAGE`：**156/156 resolved**
- `NEAR_SURFACE_MOLECULAR_BOUNDARY_ANCHOR_PROVENANCE`：PASS
- `NEAR_SURFACE_MOLECULAR_BOUNDARY_FROZEN_10M_TOLERANCE`：PASS
- `NEAR_SURFACE_MOLECULAR_BOUNDARY_BRIDGE_PROVENANCE`：PASS

因此：

> **R5.7.37 Near-Surface Molecular Boundary Closure = FIELD PASS / FIELD CLOSED**

### 二、10 m tolerance 沒有被放寬

CASE 中 `glow_observer_molecular_lowest_endpoint_tolerance_km` 全部仍為：

`0.01 km = 10 m`

Integrity 直接驗證：

`min=0.01; max=0.01`

所以本版並不是把 10 m 偷改成 20 m、25 m 或 50 m。

### 三、ML137 近地 O3 anchor

本次 CAMS 新增的：

`O3_NEAR_SURFACE_MODEL_LEVEL_137`

兩個 forecast time request 全部成功。

Gas profile 共建立 **990 個 READY near-surface anchor rows**。

實際 anchor 高度範圍：

- 約 **10.370–10.449 m AGL**

固定 hybrid pressure ratio：

- **0.998815**

Surface thermodynamic evidence：

- surface pressure：約 999.92–1013.31 hPa
- temperature：約 298.78–301.05 K
- RH：約 54.96–82.56%

Native ML137 O3 mass mixing ratio：約：

- 6.13e-08 ～ 1.40e-07 kg/kg

全部保留：

`CAMS_MODEL_LEVEL_137_OZONE_NATIVE_NEAR_SURFACE_ANCHOR`

以及：

`HYPSOMETRIC_FROM_SURFACE_PRESSURE_AND_2M_TEMPERATURE`

provenance。

### 四、原 100 km / 3.75 km 缺口已真正閉合

上一版 R5.7.36：

- deep-range molecular：153/156
- unresolved：3 rows
- 集中於 −6° × 三方向 × 100 km / 3.75 km

R5.7.37：

- **156/156 resolved**

CASE 仍保留 pressure-level-only 原始缺口：

- 0° 到 −5.5°：約 **9.713 m**
- −6°：約 **21.319 m**

因此 −6° 的 21.319 m 缺口沒有被消失或改寫。

真正閉合方法是：

`ML137 約 10.4 m anchor → lowest native pressure-level`

形成真實 bracket。

例如中心方向近地 profile：

0°：
- ML137：約 10.415 m
- 1000 hPa：約 84.334 m

−6°：
- ML137：約 10.403 m
- 1000 hPa：約 95.939 m

原先約 74.62 m 的 LOS midpoint 因此落在兩個真實原生/推導 anchor 之間，而不是靠 downward extrapolation。

### 五、Bridge provenance

Integrity：

`bridged_rows=39; resolved=39`

也就是 13 個太陽角 × 3 個方向的 100 km / 3.75 km observer geometry 都有明確 near-surface bridge evidence。

每一組：

- `glow_observer_near_surface_boundary_bridge_segment_count = 1`
- 原 pressure-level-only gap 仍被保存
- molecular endpoint tolerance 仍是 0.01 km

### 六、Scatter→Observer 完整率改善

R5.7.36：

- FULL：1053 / 1092
- PARTIAL：39 / 1092

其中 36 rows 雖 Rayleigh / gas path 已 resolve，但整體仍保留 `GAS` Missing；另 3 rows 為 `GAS;GAS_SPECIES;RAYLEIGH`。

R5.7.37：

- **FULL：1092 / 1092**
- PARTIAL：0

因此 near-surface closure 不只修掉最後 3 個硬 molecular FAIL，也把全部 39 個同一幾何的 observer gas evidence 正式閉合。

### 七、Aerosol scattering handoff

R5.7.36：

- READY：136
- UNRESOLVED：956

R5.7.37：

- READY：**143**
- UNRESOLVED：**949**

剩餘 949 rows 的 missing reason 全部是：

`SUN_TO_SCATTER_EXTINCTION`

沒有 blank missing reason，也沒有因 Observer path closure 而錯誤 promotion。

### 八、Formation / Canvas 未被污染

與同一天 R5.7.36 CASE 逐欄比較：

- `v1_canvas_candidates.csv`：**完全一致**
- `v1_formation.csv`：**完全一致**

因此 R5.7.37 的 near-surface molecular closure 沒有改寫 Formation 或 Canvas science。

Viewing 六波段 mean transmission 因近地 molecular profile 更完整而有小幅數值更新，最大相對差約 **0.052%**；但：

- `viewing_state`：不變
- Photography decision 狀態：不變

### 九、CAMS request

本次 CAMS 共 **10 requests**：

兩個 forecast time × 五個 roles：

1. O3_PRESSURE_LEVEL
2. O3_NEAR_SURFACE_MODEL_LEVEL_137
3. SPECTRAL_COLUMN_AOD
4. NATIVE_AEROSOL_532NM_PRESSURE_LEVEL
5. AEROSOL_SCATTERING_COLUMN_PROPERTIES

結果：

- **10/10 OK**
- timeout：0
- request reattach：0

### 十、Runtime 新證據：Post-success Download Retry

本次 f024 `SPECTRAL_COLUMN_AOD`：

- ADS remote queue：約 16.36 s
- ADS remote running：約 4.78 s
- remote lifecycle：約 **21.14 s**
- 但 worker elapsed：約 **153.55 s**

`cams_worker_checkpoints.json` 明確記錄：

- `502 Bad Gateway`
- `Retrying in 120 seconds`

因此再次證明：

> Remote job 已 successful，但 download 階段遇到 HTTP 502，client 固定等待 120 秒後才重試。

這不是 ADS queue 慢，也不是重新 submit request 的問題。

下一個 runtime 主線應為：

**CAMS Post-success Download Recovery**

要求：

- 保留同一 request ID
- remote successful 後不重新 submit
- download retry 與 remote lifecycle 分離記錄
- 有界 retry/backoff
- 不讓下載階段的 502 被誤算為 ADS queue/running timeout

### 十一、效能

- `CAMS_PREFETCH_TOTAL`：約 466.51 s
- `ALL_ANGLES_PHYSICS_TOTAL`：約 348.86 s
- `TOTAL_ANALYSIS_CORE`：約 1112.18 s
- `TOTAL_TO_CASE_ARCHIVE`：約 **1139.38 s ≈ 18 分 59 秒**
- Peak RSS：約 **915.54 MB**

記憶體仍在約 900 MB 監測區間，未發生 OOM，但後續仍應保留 runtime/memory optimization 項目。

### 十二、目前版本判定

- R5.7.35 Aerosol Scattering Physics：FIELD PASS
- R5.7.35.1 Missing-Reason Handoff：FIELD PASS
- R5.7.35.2 Zero-Eligible Viewing precipitation semantics：已納入後續版
- R5.7.36 Formation Canvas Eligibility：Code/Regression CLOSED；本台灣 CASE無回歸
- **R5.7.37 Near-Surface Molecular Boundary Closure：FIELD CLOSED**

下一個主線：

> **CAMS Post-success Download Recovery**

