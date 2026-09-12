# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.3

## Historical Replay Empty Cloud-Volume Guard Hotfix

- 修正 2026-08-30 歷史回測在 Twilight Glow → Viewing six-band cloud extinction 的 `KeyError: 'direction_offset_deg'`。
- root cause：歷史/部分 provider replay 可產生 headerless empty cloud-layer DataFrame；舊程式仍直接索引 `direction_offset_deg`。
- 新增 `VIEW_CLOUD_VOLUME_UNRESOLVED` fail-closed 狀態。
- Missing cloud volume 不再被當成 Clear，也不再終止 worker。
- 完整 schema、只是該 time/angle/direction 沒有 blocker row時仍保留 `VIEW_CLOUD_PATH_CLEAR`。
- `_group_route()` 同步做缺欄位防護。
- 不修改 Production COT、Shadow COT science baseline、Formation、Viewing RT 公式、Twilight Glow、Photography 或六波段契約。

## Field trigger
使用者於 2026-09-12 對 2026-08-30 事件連續三次歷史回測；CAMS `AEROSOL_SCATTERING_COLUMN_PROPERTIES` 已 COMPLETED，但 analysis worker 約 376.5 秒後在 `viewing_spectral.py` 因缺 `direction_offset_deg` 終止。此故障屬程式 schema guard 缺口，不等同 CAMS/GFS 歷史資料不可用。

## Regression
Working-tree：598/598 PASS；FULL-CLEAN fresh-extract：598/598 PASS；1 個既有 pandas FutureWarning，非失敗；Release Gate CLOSED。
