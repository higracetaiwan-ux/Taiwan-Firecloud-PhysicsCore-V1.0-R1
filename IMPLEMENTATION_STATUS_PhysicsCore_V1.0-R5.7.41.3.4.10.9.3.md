# Implementation Status — V1.0-R5.7.41.3.4.10.9.3

## 名稱

**Observer Near-field Cloud Environment Diagnostic**

## 狀態

**REGRESSION PASS / FIELD RETEST CANDIDATE**

## 已完成

- 新增 `firecloud/observer_nearfield_cloud_environment.py`。
- 直接使用已存在的 exact-time Viewing/Glow route snapshots，不新增 provider request。
- 點級保存 0–100 km：low/mid/high cloud cover、visibility、RH2m、precipitation、native cloud base/top/thickness/completeness。
- 新增 coarse ↔ native relation：
  - `COARSE_AND_NATIVE_LOW_CLOUD`
  - `COARSE_LOW_CLOUD_NATIVE_NO_COLUMN_AT_THRESHOLD`
  - `COARSE_LOW_CLOUD_NATIVE_UNAVAILABLE`
  - `NATIVE_LOW_CLOUD_COARSE_EXACT_ZERO`
  - 其他 Missing/Unresolved 狀態。
- 新增距離摘要：Near Observer 0–10、Primary >10–40、Extended >40–100 km。
- 新增 Analysis Integrity guards，確保 diagnostic 不可合成 τ/COT、不升 Formation、不要求 formed target。
- CASE archive 將兩個新 CSV 列為 required evidence member。
- `.10.9.2` zero-target Shadow collection integrity fix 已包含。

## Frozen science audit

相對 `.10.9.2`，以下關鍵 science modules byte-identical：

- `firecloud/gas_rt.py`
- `firecloud/formation.py`
- `firecloud/viewing.py`
- `firecloud/viewing_spectral.py`
- `firecloud/twilight_glow.py`
- `firecloud/canvas_cot_semantic_migration.py`
- `firecloud/config.py`
- `firecloud/red_light_availability.py`
- `firecloud/photography_decision.py`

## 測試

- 新增 near-field diagnostic tests：6/6 PASS。
- 完整 working-tree regression：**703/703 PASS**。
- 僅 1 個既有 pandas FutureWarning。

## Field gate

尚需 `.10.9.3` 實際 CASE 驗證，因此目前不能標 FIELD PASS。
