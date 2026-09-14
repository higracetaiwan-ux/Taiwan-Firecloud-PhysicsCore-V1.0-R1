# `.10.9.7` TWS106 CAMS Exact-Reuse Offline Proxy

資料基礎：`.10.9.6` TWS106 2026-09-14 sunset 正式 CASE。

## Provider request overlap

同一 CAMS valid-time request 中：

- `SPECTRAL_COLUMN_AOD` 要求 AOD 550/645/670/800 nm，elapsed 47.275 s。
- `AEROSOL_SCATTERING_COLUMN_PROPERTIES` 同樣要求 AOD 550/645/670/800 nm，另加 AOD532、SSA、asymmetry；date/time/lead/area 與 spectral request 相同。

正式 exported CAMS route snapshots 中，2691/2691 rows 的 `aod550/aod645/aod670/aod800` 都有數值，代表該 CASE 符合 `.10.9.7` exact-reuse eligibility。

## 預期 runtime 行為

若 `.10.9.7` Field run 的 scattering response 同樣完整：

- dedicated `SPECTRAL_COLUMN_AOD` ADS network request 不送出；
- request audit 保留一列 `final_status=EXACT_SOURCE_REUSE`；
- `exact_source_role=AEROSOL_SCATTERING_COLUMN_PROPERTIES`；
- CAMS provider request count 由 5 降為 4；
- 以 `.10.9.6` 同一 CASE 的 provider elapsed 作 attribution，可消除 47.275 s 的重複 spectral request cost；實際 wall-clock 仍受 ADS queue/network 影響，須以 Field CASE 驗證。

## 科學限制

只允許相同 CAMS provider、相同 valid time、相同 route request 中的 native AOD550/645/670/800 exact handoff。不做 Angstrom 造值、不做時間替代、不把 AOD 當 3-D aerosol profile。
