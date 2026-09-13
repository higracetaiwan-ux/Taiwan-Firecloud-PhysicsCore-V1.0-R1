# Red-Light Precipitation Horizontal-Support Ray Reuse Spec — R5.7.41.3.4.9.2

## 目的
消除 Red-Light precipitation native 3-D hydrometeor ray integration 中，同一方向、同一 horizontal support interval、不同 pressure-level cells 之間重複的 curved-Earth ray sampling。

## Frozen science contract
本版不得改變：
- GFS RWMR / SNMR / GRLE native hydrometeor evidence；
- Qext=2 Tier-1 large-particle extinction；
- rain/snow/graupel assumed effective radii與密度；
- 17-point Sun→CloudBase curved-Earth ray sampling；
- pressure-level vertical cells；
- layer intersection / sampled slant-path integration；
- 六波段 550/575/600/650/700/750 nm；
- Missing ≠ Clear ≠ Zero；
- surface precipitation rate 不得轉為 tau；
- Formation / Viewing / Twilight Glow 分離。

## Runtime change
舊流程：對每一個 pressure-level cell 呼叫一次 `sample_sun_ray_segment()`。同一 horizontal support 的垂直層因此重複計算相同 `(td, tz, a, b, solar_altitude, 17 points, Earth radius)`。

新流程：
1. 將 native hydrometeor cells 依 `(support_start_km, support_end_km)` 分組；
2. 每一 horizontal support 只執行一次原本完全相同的 17-point ray sampling；
3. 同一 support 內所有 pressure-level cells 仍依原始順序逐層判斷 z intersection；
4. 每一交會層仍各自執行原本的 `sampled_segment_path_km()` 與 extinction accumulation；
5. tau accumulation order 保持不變。

## Exact-equivalence gate
- legacy-cell integrator vs grouped integrator tuple exact equality；
- prepared / direct precipitation DataFrame `check_exact=True`；
- ray sample call-count test：每 horizontal support 一次，而非每 vertical cell 一次。

## Field gate
使用 TWS056 / 2026-09-13 sunset：
- `RED_LIGHT_COMPONENT_PRECIPITATION_PATH` 必須相較 `.3.4.9` / `.3.4.9.1` 的 ~110 s 明顯下降；
- Red-Light science CSV 必須維持 exact-equivalent；
- Analysis / CASE Integrity 不得 regression。
