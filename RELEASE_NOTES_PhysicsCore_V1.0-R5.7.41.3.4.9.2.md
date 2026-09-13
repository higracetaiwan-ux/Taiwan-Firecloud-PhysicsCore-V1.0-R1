# Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.9.2 — Release Notes

## 主題
Red-Light Precipitation Horizontal-Support Ray Reuse

## 背景
`.3.4.9.1` Field CASE 證明 prepared native hydrometeor context cache 雖然 12/12 cross-angle 命中，但 precipitation path 仍為 109.515 s，與 `.3.4.9` 110.323 s 幾乎相同。主要成本位於 ray integration，而不是 native context preparation。

## 本版變更
- 同一 direction / horizontal support interval 的 pressure-level cells 共用一次 17-point `sample_sun_ray_segment()`。
- 垂直層仍逐層 intersection 與 slant-path integration。
- 原始 cell/tau accumulation order 保持。
- prepared native context 內加入 private horizontal-support plan；不輸出成 science data。

## 不變項
無 science threshold / weighting / spectral / geometry / Missing semantics 改動。Science baseline 維持 `R5.7.41.2_SHADOW_COT_AB_FROZEN`。

## 驗證
- targeted regression：13/13 PASS
- full regression：647/647 PASS
- grouped vs legacy integrator exact equality
- direct vs prepared precipitation DataFrame `check_exact=True`
- synthetic multi-level integrator benchmark 約 13×（僅結構性本機 benchmark，不作 Field PASS 宣稱）

## 狀態
Field-Test Candidate。需 TWS056 同事件 CASE 驗證 precipitation component 真實下降。
