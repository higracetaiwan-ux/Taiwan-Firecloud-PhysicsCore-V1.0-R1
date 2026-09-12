# Taiwan Firecloud PhysicsCore — R5.7.41.3.4.8
## Viewing Path Geometry Runtime Optimization Phase 1

### 目的
在不修改 `R5.7.41.2_SHADOW_COT_AB_FROZEN` 科學基線的前提下，針對 R5.7.41.3.4.7 profiler 實測最大 Viewing/Photography component：`build_viewing_path_geometry()` 做 exact-equivalent runtime optimization。

### Field profiler 依據
2026-09-12 Sunset｜TWS106 高美濕地｜R5.7.41.3.4.7.1：
- `AGGREGATION_VIEWING_AND_PHOTOGRAPHY` = 130.925452 s
- `VIEWING_COMPONENT_PATH_GEOMETRY` = 56.920498 s（最大戶，約 43.5%）
- `VIEWING_COMPONENT_SPECTRAL_EXTINCTION` = 40.710611 s（約 31.1%）
- `VIEWING_COMPONENT_PRECIPITATION_EVIDENCE` = 15.090977 s
- `VIEWING_COMPONENT_TARGET_OPTICS_RECONCILIATION` = 9.206403 s
- `VIEWING_COMPONENT_PREPARE_SPECTRAL_RUNTIME_CONTEXT` = 8.543756 s

### Phase 1 改動
1. 每個 time / angle / direction transect 建立 immutable numeric plan。
2. projected support interval 只計算一次，不再於每個 target/sample 重掃 DataFrame。
3. Cloud Fraction vertical-continuity neighbours 只建立一次，保留原始 row order 與 nearest-distance tie semantics。
4. blocker candidate selection 改為 numeric array mask。
5. 每個 blocker 的 17-point curved-Earth LOS sample 同時供 intersection qualification 與 crossing-position CF interpolation 使用，不再重複取樣兩次。

### 凍結不變
- 7 個 target-height samples 不變。
- 每段 17-point curved-Earth LOS sampling 不變。
- `VERTICAL_CONTINUITY_MIN_OVERLAP = 0.50` 不變。
- CF 僅為 Viewing occupancy proxy，非 COT。
- Missing occupancy 不得轉成 clear sky。
- Formation / Sun→CloudBase / Earth Shadow / six-band / Photography decision 全部不變。

### Exact-equivalence gate
TWS106 實際輸入：4940 cloud-layer rows、1131 Canvas targets、39 transect groups。
- Legacy local benchmark: 13.210 s
- R5.7.41.3.4.8 local benchmark: 1.657 s
- speedup ≈ 7.97×
- 1131 × 25 geometry output：逐欄 0 differences（NaN 同義）。

### 後續
Field 部署後重新跑同一 TWS106 CASE，確認 Streamlit Cloud 上的實際 `VIEWING_COMPONENT_PATH_GEOMETRY` 時間，再決定下一個 runtime optimization target。不得用本機 benchmark 直接宣稱 Field speedup。
