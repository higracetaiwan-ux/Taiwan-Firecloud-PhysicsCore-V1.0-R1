# Taiwan Firecloud PhysicsCore — V1.0-R5.7.41.3.4.9.1

## Red-Light Precipitation Native Context Reuse

R5.7.41.3.4.9 Field profiler 已定位 `RED_LIGHT_COMPONENT_PRECIPITATION_PATH` 為 Red-Light 最大 runtime hotspot：13 個角度累計 110.323 s，占八個 profiler component 約 74.0%。

本版只做 exact-equivalent runtime reuse：相同 GFS forecast snapshot 的 native hydrometeor geometry/optics context 僅建立一次，後續角度直接重用。沒有更改任何 Formation、Viewing、Glow、Shadow、COT、hydrometeor optics、ray sampling、六波段或 Missing semantics。

測試：643/643 PASS；既有 pandas FutureWarning 1。
