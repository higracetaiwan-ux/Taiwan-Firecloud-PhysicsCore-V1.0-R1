# Red-Light Precipitation Native Context Reuse — R5.7.41.3.4.9.1

## 目的
依 R5.7.41.3.4.9 Field profiler，Red-Light Reference Availability 的最大 runtime hotspot 是 `RED_LIGHT_COMPONENT_PRECIPITATION_PATH`。TWS056 2026-09-13 sunset CASE 13 個角度累計 110.323 s，約占八個 component 總時間 74.0%。

## 根因
同一事件 13 個角度共用同一 GFS forecast snapshot cache key `('2026-09-13T00:00:00+00:00', 9)`，但 precipitation path 每次都重新解析相同 pressure-level native hydrometeor volume（RWMR/SNMR/GRLE + temperature + geopotential-height）。

## 修正
加入 `prepare_native_hydrometeor_context()`，並以 forecast `cache_key` 建立 cross-angle runtime cache。第一個角度建立 context，後續角度重用完全相同的 prepared cells/meta。

## 不變的科學契約
- Surface precipitation rate 不轉成 optical depth。
- 只使用 forecast-native RWMR/SNMR/GRLE。
- Missing != Zero != Clear。
- LARGE_PARTICLE_GREY_EXTINCTION_TIER1_QEXT2_ASSUMED_REFF 不變。
- Sun→CloudBase ray geometry、17-point sampling、intersection 判定不變。
- 六波段 550/575/600/650/700/750 nm 不合併。

## Release gate
prepared-context 與 legacy rebuild output 必須 `check_exact=True` 完全一致。
