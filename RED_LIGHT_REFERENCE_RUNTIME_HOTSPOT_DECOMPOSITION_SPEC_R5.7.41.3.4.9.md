# Taiwan Firecloud PhysicsCore — R5.7.41.3.4.9
## Red-Light Reference Availability Runtime Hotspot Decomposition

## 目的
R5.7.41.3.4.8 已在 2026-09-13 Sunset / TWS056 淡水漁人碼頭 Field CASE 關閉 Viewing Geometry Phase 1：第二次同 deployment warm run 的 Viewing Geometry 約 1.973 s，而 `RED_LIGHT_REFERENCE_AVAILABILITY` 約 153.926 s，成為目前最大的可分解 runtime stage。

本版只做 profiler decomposition，不做物理或演算法最佳化。

## 八個 component profiler
每個 solar angle 都會輸出：

1. `RED_LIGHT_COMPONENT_BUILD_RECEIVERS`
2. `RED_LIGHT_COMPONENT_SPECTRAL_RT`
3. `RED_LIGHT_COMPONENT_CLOUD_PATH`
4. `RED_LIGHT_COMPONENT_VIRTUAL_CANVAS`
5. `RED_LIGHT_COMPONENT_PRECIPITATION_PATH`
6. `RED_LIGHT_COMPONENT_MERGE`
7. `RED_LIGHT_COMPONENT_SIX_BAND_AVAILABILITY`
8. `RED_LIGHT_COMPONENT_PATH_STATE`

所有 component rows 均標記：

`R5741349_COMPONENT_PROFILE_ONLY`

## 凍結條件
本版不得改變：
- reference receiver 數量、距離、方向或 cloud-base sampling；
- 六波段 550/575/600/650/700/750 nm；
- Sun→reference receiver geometry；
- cloud / hydrometeor / precipitation blocking semantics；
- Missing ≠ Clear ≠ Zero；
- Cloud Fraction / RH 不得補造 tau；
- Formation / Viewing / Twilight Glow / Photography branch separation；
- Earth Shadow / COT / Shadow candidate semantics；
- `RED_LIGHT_PATH_*` 狀態判定。

## Release Gate
- profiler 開啟與不開啟時，Red-Light science DataFrame 必須 exact-equivalent；
- full regression 必須 PASS；
- fresh-extract regression 必須 PASS；
- Field CASE 先量測再決定下一個 optimization target，不得預設 Spectral RT 為最大戶。
