# Taiwan Firecloud PhysicsCore — Current Project State

## 現行候選版
V1.0-R5.7.41.3.4.9.1 — Red-Light Precipitation Native Context Reuse

## Field evidence
- R5.7.41.3.4.8 Viewing Path Geometry Optimization：FIELD PASS。
- Persistent provider cache：同一 deployment 第二跑 CAMS/DWD 皆成功命中。
- R5.7.41.3.4.9 Red-Light profiler：PRECIPITATION_PATH 110.323 s / 74.0%，SPECTRAL_RT 22.053 s / 14.8%。

## 本版目標
以 forecast snapshot cache key 重用 prepared native hydrometeor context；不改任何 precipitation physics。

## 下一步
用 TWS056 2026-09-13 sunset 跑 .3.4.9.1 CASE，確認 precipitation component 顯著下降，並檢查 Integrity 與 Red-Light science output。若 Field PASS，再重新排序下一個 hotspot。
