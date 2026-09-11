# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3

## Shadow Validation Collection Readiness / Shared Scenic Spot Selector

新增共用 187 景點 GPS registry、區域＋景點可搜尋選單與自訂座標 fallback。分析 request / CASE 現在保存穩定 `site_id`、景點名稱、區域、GPS、location source 與 registry version。

新增 CASE artifacts：
- `shadow_validation_case_manifest.csv`
- `shadow_validation_cohort_summary.csv`
- `shadow_validation_ground_truth_template.csv`
- `shadow_validation_runtime_summary.csv`
- `analysis_request.json`

新增 science-baseline freeze guard：第一批 Shadow cohort 固定 `R5.7.41.2_SHADOW_COT_AB_FROZEN`。任何 Production COT switch、COT promotion、Formation promotion 或 Production COT source 漂移均 fail-close。

新增 `tools/aggregate_shadow_validation_cases.py`，可離線合併多個 CASE 的 cohort summary，不呼叫 GFS/CAMS。

本版不修改 Production COT、Formation、Viewing、Glow、Photography 或既有物理門檻。

Release gate CLOSED：working-tree regression 589/589 PASS；FULL-CLEAN fresh-extract regression 589/589 PASS；1 個既有 pandas FutureWarning，非失敗。
