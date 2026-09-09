# PhysicsCore V1.0-R5.7.29.1 Implementation Status

## Completed

- [x] R5.7.29 CASE archive forensic
- [x] native GFS hydrometeor inventory/completeness verification
- [x] Viewing spool cleanup/drain ordering fix
- [x] precipitation evidence pre-export Integrity handoff
- [x] per-target precipitation coverage hard guard
- [x] RWMR/SNMR/GRLE READY handoff hard guard
- [x] original R5.7.29 CASE immutable re-audit exposes the regression
- [x] targeted regression：27 passed / 0 failed
- [x] working-tree regression：474 passed / 0 failed
- [x] FULL-CLEAN extraction regression：474 passed / 0 failed

## Required field validation

以 R5.7.29.1 真實部署重新產生 sunset CASE，確認：

- precipitation evidence row coverage 等於 eligible Viewing target coverage；
- RWMR/SNMR/GRLE READY 時沒有 `VIEW_PRECIPITATION_VOLUME_UNRESOLVED`；
- 新增兩項與既有五項 `VIEWING_SIX_BAND_*` Integrity checks 通過；
- Full rows 的六波段 total tau / transmission arithmetic closure 通過；
- Formation-first 與 13-angle Photography 不變。
