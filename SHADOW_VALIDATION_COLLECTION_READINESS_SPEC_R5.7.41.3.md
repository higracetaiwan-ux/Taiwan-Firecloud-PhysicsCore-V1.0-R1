# Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3
## Shadow Validation Collection Readiness / Shared Scenic Spot Selector

### 目的
在正式累積 12–16 個 sunrise / sunset Shadow Mode CASE 前，先凍結收集契約與地點 identity，避免同一景點因座標手動輸入誤差、程式版本變動或 CASE metadata 不完整而失去可比性。

### Shared Scenic Spot Registry
來源為台灣晨昏攝影景點母資料庫 V2.2，程式內固定 registry version：
`TAIWAN_DAWN_DUSK_SCENIC_SPOTS_V2.2_187`。

每個預設景點保存：
- `site_id`
- `site_name`
- `site_region`
- `site_county_area`
- latitude / longitude
- GPS status / type
- sunrise / sunset suitability
- source provenance

`site_id` 以既有母資料庫編號生成穩定識別，例如高美濕地 = `TWS106`。

### UI
事件設定提供：
1. 景點選單：區域 → 可搜尋景點 → 自動帶入 GPS。
2. 自訂座標：保留臨時機位，`site_id=MANUAL`，不得冒充任何 preset identity。
3. 景點日出／日落標記若與目前 event 不一致，只提示，不阻擋物理分析。

### CASE Collection Artifacts
新增：
- `shadow_validation_case_manifest.csv`
- `shadow_validation_cohort_summary.csv`
- `shadow_validation_ground_truth_template.csv`
- `shadow_validation_runtime_summary.csv`
- `analysis_request.json`

CASE 檔名加入 `site_id`。

### Science Baseline Freeze
第一批 Shadow cohort 固定：
`R5.7.41.2_SHADOW_COT_AB_FROZEN`

收集期間：
- Production COT source 必須保持 `LEGACY_CF_SCALED_GRID_CELL_MEAN`
- Shadow candidate source = `IN_CLOUD_EXACT_ENVELOPE_ASSUMED_REFF`
- `production_switch_performed=False`
- `cot_promotion_allowed=False`
- `formation_promotion_allowed=False`

任一違反均使 Shadow collection CASE guard FAIL。

### Ground Truth Template
每個 CASE 自動附一列待填模板，預留：
- actual firecloud strength: NONE / WEAK / MODERATE / STRONG / EXTREME / UNKNOWN
- observed canvas type
- viewing quality
- photo reference
- observer notes

### Runtime
本版只新增 runtime collection summary，不改 provider sampling / fetch / decode / physics execution。效能改善若要進行，必須另行證明不影響 cohort science baseline。

### 不修改
- Production Target COT
- Formation
- Viewing
- Twilight Glow
- Photography
- 六波段、太陽角度、Canvas / blocker、Missing semantics
