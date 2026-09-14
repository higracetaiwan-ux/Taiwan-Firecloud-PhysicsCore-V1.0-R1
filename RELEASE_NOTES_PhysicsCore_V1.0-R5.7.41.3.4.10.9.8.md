# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.9.8

## DWD Cross-Release Exact Cache + HTTPS Connection Reuse

`.10.9.7` TWS089 Field 將下一個 runtime hotspot 定位到 DWD ICON secondary native optics：356 network attempts、約 436.7 MB、158.752 s。

本版：

- 將 DWD durable raw/decoded exact cache 的預設 scope 改為 user-level stable cache，避免 full replacement 新資料夾把 exact provider objects 重新冷啟動；
- 保留 `FIRECLOUD_STATE_DIR` explicit contract 與更細的 DWD cache env overrides；
- DWD per-level HTTP 改為 thread-local Session keep-alive；
- FIELD_FETCH audit 新增 shared-cache scope / connection reuse provenance；
- 不減 model levels、不跨 lead、不改 provider bytes/values/geometry/COT。

Science baseline 不變：`R5.7.41.2_SHADOW_COT_AB_FROZEN`。
