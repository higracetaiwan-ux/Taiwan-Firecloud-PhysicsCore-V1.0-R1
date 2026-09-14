# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.10

## Ice Cloud Spectral Optics Shared Module Phase 1

本版正式停止把 runtime 效能優化當主線，回到 PhysicsCore 科學能力建設。Science baseline 維持 `R5.7.41.2_SHADOW_COT_AB_FROZEN`。

### 新增

- `firecloud/ice_cloud_spectral_optics.py`
- 六波段：550/575/600/650/700/750 nm
- calibrated Ice Optics LUT schema/validator
- Yang/Bi/TAMU `isca.dat` normalizer
- `Qext × A / (rho_ice × V)` → mass extinction coefficient `k_ext [m²/kg]`
- `tau_ice = IWP × k_ext`
- `T_ice = exp(-tau_ice)`
- effective diameter `1.5 V/A` 與 half-radius coordinate，明確標示為 geometry-derived coordinate
- strict Missing/Zero semantics
- WINDY shared CSV/JSON contract `FIRECLOUD_ICE_OPTICS_V1`
- CASE artifacts：
  - `v1_ice_cloud_spectral_optics_runtime.csv`
  - `v1_ice_cloud_spectral_optics_summary.csv`
  - `v1_windy_ice_optics_summary.csv`
  - `ice_cloud_spectral_optics_contract.json`
  - `windy_firecloud_ice_optics_summary_v1.json`
- UI 可直接下載 WINDY Ice Optics CSV/JSON
- source template/manifest + `tools/build_ice_optics_lut_from_tamu.py`

### Integrity

新增：

- `ICE_CLOUD_SPECTRAL_OPTICS_SIX_BAND_CONTRACT`
- `ICE_CLOUD_SPECTRAL_OPTICS_ROLE_SEPARATION`
- `ICE_CLOUD_SPECTRAL_OPTICS_MISSING_SEMANTICS`
- `ICE_CLOUD_SPECTRAL_OPTICS_SUMMARY`
- `WINDY_ICE_OPTICS_EXPORT_CONTRACT`

### 不變

- Frozen Formation / Viewing / Twilight Glow
- Production/Shadow COT
- Red-Light Availability
- Earth Shadow / Dynamic Corridor/REZ
- 六波段 gas/aerosol science
- CLWMR/ICMR threshold
- `Missing != Clear != Zero`

Phase 1 的 Ice Optics 結果不參與任何 Physics decision。
