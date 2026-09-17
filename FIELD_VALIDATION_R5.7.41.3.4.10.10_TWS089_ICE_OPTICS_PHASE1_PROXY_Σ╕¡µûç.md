# Offline Proxy Validation — R5.7.41.3.4.10.10 Ice Optics / WINDY Shared Contract

基礎 CASE：`.10.9.9` TWS089 2026-09-15 sunrise。

此 proxy 只把現有 `native_gfs_cloud_columns.csv` 餵入新的 Phase 1 shared module，不改任何原 CASE science。

## 結果

- Ice optics runtime：2691 rows
- Band summary：78 rows
- WINDY compact summary：78 rows
- 正 IWP columns：1713 rows
- `ICE_OPTICS_LUT_UNAVAILABLE`：1713 rows
- `NO_ICE_CONDENSATE_AT_NATIVE_STATE`：679 rows
- `ICE_IWP_INCOMPLETE_NATIVE_VERTICAL_SUPPORT`：299 rows
- 正 IWP 且未 ready rows 的 spectral tau 非空值：0

距離帶 summary：65 個 band/time groups 為 `ICE_SIX_BAND_OPTICS_INCOMPLETE`；13 個為 `NO_ICE_CONDENSATE_IN_BAND`。

這證明 Phase 1 的 fail-close 語意正確：現有 CASE 雖有大量 native IWP 正值，但因 calibrated Ice Optics LUT 與 native/calibrated r_eff/habit 尚未建立，程式不會沿用舊 fixed 30 µm/Qext≈2 假裝成正式六波段 ice tau。

## WINDY

JSON/CSV 皆帶：

- `FIRECLOUD_ICE_OPTICS_V1`
- PhysicsCore version
- frozen science baseline
- 550/575/600/650/700/750 nm
- LUT readiness
- `physics_promotion_allowed=false`

因此 WINDY 外掛可先實作 schema/UI；之後 calibrated LUT ready 時不需改共用 contract。
