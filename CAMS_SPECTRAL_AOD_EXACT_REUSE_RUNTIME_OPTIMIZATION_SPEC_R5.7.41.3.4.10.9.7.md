# R5.7.41.3.4.10.9.7 — CAMS Spectral AOD Exact Reuse + GFS Merge Defragmentation

## 目的

降低 Production runtime，不修改 `R5.7.41.2_SHADOW_COT_AB_FROZEN` 科學規則。

## CAMS exact-source reuse

`AEROSOL_SCATTERING_COLUMN_PROPERTIES` 與 `SPECTRAL_COLUMN_AOD` 在相同 CAMS run / lead / route bbox 下，都要求 provider-native：

- AOD 550 nm
- AOD 645 nm
- AOD 670 nm
- AOD 800 nm

`.10.9.7` 先執行 scattering-column role。只有當四個波長在**所有 requested point_id** 都為有效數值時，`SPECTRAL_COLUMN_AOD` 才以 `EXACT_SOURCE_REUSE` 完成，不再送出第二個 ADS request。

禁止：

- 時間插值來取代 exact-valid-time request
- Ångström 合成取代 provider-native source
- AOD550 單波段推造其他波段
- 不完整 scattering response 冒充完整 spectral response

若任一 route point 或任一 550/645/670/800 nm 欄位不完整，立即回到原本 dedicated `SPECTRAL_COLUMN_AOD` request。

新增 provenance：

- `cams_spectral_aod_exact_reuse`
- `cams_spectral_aod_exact_reuse_source`
- request audit `final_status=EXACT_SOURCE_REUSE`
- `exact_source_role=AEROSOL_SCATTERING_COLUMN_PROPERTIES`
- Analysis Integrity `CAMS_SPECTRAL_AOD_EXACT_REUSE_PROVENANCE`

## GFS DataFrame defragmentation

`merge_native_into_snapshot()` 原本逐欄插入 canonical pressure-profile 欄位，TWS106 `.10.9.6` 正式 CASE 大量出現 pandas `DataFrame is highly fragmented` PerformanceWarning。

`.10.9.7` 將原本需要新增的 canonical columns 先集中建立，再一次 `pd.concat(axis=1)`，之後只做 existing-column in-place backfill。Provider precedence、Missing semantics、所有數值公式不變。

## Frozen science

以下不變：Formation、Viewing、Twilight Glow、六波段、Dynamic Corridor/REZ、Canvas、Production/Shadow COT、CLWMR/ICMR threshold、red-light physics、Photography Decision。
