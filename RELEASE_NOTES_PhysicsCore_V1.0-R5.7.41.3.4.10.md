# Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10 — Release Notes

## 主題
Twilight Glow Runtime Hotspot Decomposition

## 背景
`.3.4.9.2` 已將 Red-Light precipitation path 從約 109.5 s 壓到約 6.8–7.6 s，Phase 2 Field PASS。第二跑顯示 Twilight Glow 約 90.98 s，成為目前最大的穩定非-provider CPU stage。

## 本版變更
- 將 Twilight Glow runtime 拆成 10 個 component profiler rows。
- `build_twilight_glow_branch()` 透過 `runtime_cache_stats["component_seconds"]` 回傳 side-channel timings。
- `model.py` 將 internal timings 與 phase1 exports / aerosol scattering / summary attach timings寫入 `performance_diagnostics.csv`。
- profiler marker: `R57413410_COMPONENT_PROFILE_ONLY`。

## 不變項
本版不做 Glow 加速、不改任何物理公式、門檻、波段、路徑、Missing semantics、Formation / Viewing / Photography 決策或 Shadow/COT。
Science baseline 維持 `R5.7.41.2_SHADOW_COT_AB_FROZEN`。

## 驗證
- Glow targeted tests: 39/39 PASS
- Full regression: 650/650 PASS
- profiler 開/關：Glow detail / summary `check_exact=True`
- 既有 pandas FutureWarning 1 個，非失敗

## 狀態
Field-Test Candidate。下一個 TWS056 CASE 用來決定 Glow 內真正最大 component；不預先假設最佳化方向。
