# Taiwan Firecloud PhysicsCore — Current Project State

> 版本：**V1.0-R5.7.41.3.4.10.10**  
> Internal：`1.0.0-R5.7.41.3.4.10.10`  
> 名稱：**Ice Cloud Spectral Optics Shared Module Phase 1**  
> Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`  
> Release state：**REGRESSION PASS / FIELD RETEST CANDIDATE**

## 已完成 Field

- `.10.9.3 = FIELD PASS + TWS111 CROSS-SITE PASS`
- `.10.9.4 = FIELD PASS`
- `.10.9.5 = FIELD PASS`
- `.10.9.6 = FIELD PASS`：TWS106 near-field GFS source underrepresentation confirmed。
- `.10.9.7 = FIELD PASS`：CAMS spectral AOD exact-source reuse confirmed。
- `.10.9.8`：DWD HTTPS transport FIELD PASS；cache-scope defect found。
- `.10.9.9 = FIELD PASS`：TWS089 2026-09-15 sunrise；CAMS pressure-level exact bundle + DWD cache-scope contract正式成立。

## `.10.9.9` TWS089 Field 基準

- Job：COMPLETED；worker 510.408 s；Core 478.618 s；Total to CASE archive 505.046 s。
- Analysis Integrity：85 PASS / 1 NOT_APPLICABLE / 0 FAIL。
- CASE Integrity：38/38 PASS。
- CAMS actual ADS jobs = 3：pressure-level chemistry/optics bundle、O3 ML137、aerosol scattering column；O3 pressure-level、Native532、Spectral AOD皆 exact-source reuse。
- DWD `shared_cache_scope/raw_cache_scope = USER_LEVEL_CROSS_RELEASE_EXACT_IDENTITY`，實際 path 位於 `~/.cache/taiwan_firecloud/dwd_icon/`；secondary prefetch 40.822 s。

## `.10.10` Ice Cloud Spectral Optics Phase 1

### 六波段與 LUT contract

固定波段：`550/575/600/650/700/750 nm`。

Normalized LUT 維度：

- wavelength
- ice habit
- surface roughness
- maximum dimension
- geometry-derived effective diameter / effective-radius coordinate
- mass extinction coefficient `k_ext [m²/kg]`
- single-scattering albedo
- asymmetry parameter
- authoritative source provenance

Phase 1 首選 authoritative source family：Yang/Bi ice-particle single-scattering database V2。release 不附帶捏造或未校準係數；提供 `tools/build_ice_optics_lut_from_tamu.py` 將原始 `isca.dat` 正規化成 Firecloud 六波段 LUT。

### 光學公式

`k_ext = Qext × A_proj / (rho_ice × V)`，目前使用與既有 PhysicsCore 一致的 `rho_ice=917 kg/m³`。

只有 IWP vertical support、effective size、habit、roughness、六波段 LUT 全部完整時才診斷：

`tau_ice(lambda) = IWP [kg/m²] × k_ext(lambda) [m²/kg]`

`T_ice(lambda) = exp(-tau_ice(lambda))`

### Missing / role separation

- `Missing != Clear != Zero`
- positive IWP + LUT / r_eff / habit / roughness 缺失 → spectral tau Missing
- vertical completeness < 1 → tau Missing
- 只有完整 vertical support 下的 exact IWP=0 才可輸出 tau=0、T=1
- 禁止 RH、Cloud Fraction、季節經驗、unlabelled fixed r_eff/habit 補造冰雲 tau
- Phase 1：`physics_role=DIAGNOSTIC_ONLY_UNASSIGNED`
- `formation_promotion_allowed=False`
- 不修改 Frozen Formation / Viewing / Twilight Glow / Red-Light / Photography / Production COT

## WINDY Firecloud Observer Shared Export

Contract：`FIRECLOUD_ICE_OPTICS_V1`。

CASE / UI 輸出：

- `v1_ice_cloud_spectral_optics_runtime.csv`
- `v1_ice_cloud_spectral_optics_summary.csv`
- `v1_windy_ice_optics_summary.csv`
- `windy_firecloud_ice_optics_summary_v1.json`
- `ice_cloud_spectral_optics_contract.json`

WINDY compact output 保留 PhysicsCore version、science baseline、六波段、LUT readiness/provenance、distance band、IWP/size/habit readiness、spectral tau/transmission readiness，以及 `physics_promotion_allowed=false`。

## TWS089 `.10.10` Offline Proxy

以 `.10.9.9` TWS089 `native_gfs_cloud_columns.csv` 餵入 Phase 1 shared module：

- runtime：2691 rows
- summary：78 rows
- WINDY summary：78 rows
- positive IWP：1713 rows
- `ICE_OPTICS_LUT_UNAVAILABLE`：1713 rows
- `NO_ICE_CONDENSATE_AT_NATIVE_STATE`：679 rows
- `ICE_IWP_INCOMPLETE_NATIVE_VERTICAL_SUPPORT`：299 rows
- positive-IWP 但未 ready 的 spectral tau 非空值：**0**

因此已證明 fail-close：現有 CASE 雖有真實 native IWP evidence，但在 calibrated LUT / effective-size / habit 尚未完成前，不會沿用 fixed 30 µm / Qext proxy 冒充正式六波段 ice tau。

## Integrity

新增：

- `ICE_CLOUD_SPECTRAL_OPTICS_SIX_BAND_CONTRACT`
- `ICE_CLOUD_SPECTRAL_OPTICS_ROLE_SEPARATION`
- `ICE_CLOUD_SPECTRAL_OPTICS_MISSING_SEMANTICS`
- `ICE_CLOUD_SPECTRAL_OPTICS_SUMMARY`
- `WINDY_ICE_OPTICS_EXPORT_CONTRACT`

## Frozen science

Science baseline 維持 `R5.7.41.2_SHADOW_COT_AB_FROZEN`。Formation=Sun→CloudBase；Viewing=Cloud→Observer；Twilight Glow獨立第三分支。六波段 gas/aerosol、Canvas、Dynamic Corridor/REZ、Earth Shadow、Production/Shadow COT、CLWMR/ICMR threshold、Missing semantics皆不變。

## 下一步

1. 用 `.10.10` 跑正式 TWS089 或 TWS106 CASE，確認新 5 個 Ice/WINDY artifacts、Integrity 與 Frozen science output無 regression。
2. 安裝/建立 authoritative six-band Ice Optics LUT；不把 27+ GB source archive直接塞入 deploy ZIP。
3. 建立冰雲 effective-size / habit / roughness provenance strategy；在沒有真實/校準來源前保持 Missing。
4. Phase 2 再評估 habit mixture / PSD、SSA、g、phase function / Legendre moments。
5. Phase 3 必須另開 release gate，經 A/B + Ground Truth 才能考慮接入 Formation blocker / illuminated Canvas / Viewing physics。
