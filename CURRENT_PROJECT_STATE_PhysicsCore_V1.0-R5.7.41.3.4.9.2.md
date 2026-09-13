# Taiwan Firecloud PhysicsCore — Current Project State

## 現行候選版
V1.0-R5.7.41.3.4.9.2 — Red-Light Precipitation Horizontal-Support Ray Reuse

## 已成立 Field evidence
- `.3.4.8` Viewing Path Geometry Optimization：FIELD PASS。
- Persistent provider cache：FIELD PASS。
- `.3.4.9` Red-Light Hotspot Decomposition：FIELD PASS；precipitation path 110.323 s / 74.0%。

## `.3.4.9.1` 結果
- prepared native hydrometeor context cross-angle cache 正常：1 MISS + 12 HIT。
- precipitation path 110.323 → 109.515 s，僅約 -0.7%。
- 判定：**NOT FIELD PASS / optimization hypothesis rejected**。
- science outputs 保持 exact-equivalent；71/71 Analysis Integrity PASS；32/32 CASE Integrity PASS。

## `.3.4.9.2` 目標
真正消除 `_integrate_sun_path()` 內同一 horizontal support across pressure levels 的重複 17-point ray sampling。垂直層與積分不刪減。

## Local gates
- targeted 13/13 PASS
- full regression 647/647 PASS
- grouped vs legacy exact equality
- synthetic integrator benchmark ~13×；不作 Field speedup 宣稱

## 下一步
部署 `.3.4.9.2`，以 TWS056 / 2026-09-13 sunset 執行 CASE。Field PASS 必須看到 `RED_LIGHT_COMPONENT_PRECIPITATION_PATH` 明顯低於 ~110 s，且 science/Integrity 無 regression。
