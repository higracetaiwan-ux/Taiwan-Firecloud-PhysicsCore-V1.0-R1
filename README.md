# Taiwan Firecloud PhysicsCore V1.0

**Current checkpoint: V1.0-R2.1 — R2 runtime foundation + non-blocking streaming CASE export.**

This is the new main-program identity. The package is a full runnable replacement built from the V8.4.16.7 compatibility baseline while the frozen PhysicsCore V1.0 architecture is refactored stage-by-stage.

See `RELEASE_NOTES_PhysicsCore_V1.0-R2.1.md` for the exact implemented boundary.

---

# Taiwan Firecloud V8.4.15 PhysicsCore

# Taiwan Firecloud V8.4.10.5 PhysicsCore

# Taiwan Firecloud V8.4.9 PhysicsCore

# Taiwan Firecloud V8.4.1 PhysicsCore

Standalone physics-first reference implementation for the current firecloud framework.

## Civil-twilight time axis

The engine now automatically solves the complete photography-relevant civil-twilight diagnostic sequence:

- 0°
- −0.5°
- −1°
- −2°
- −3°
- −4°
- −5°
- −6°

These checkpoints are intentionally separated from the core score domain:

- **Horizon baseline:** 0°
- **Firecloud Core:** −0.5° through −4°
- **Late Glow / Third Burn diagnostic:** −4° through −6°

−4° is an intentional transition overlap. Expanding the diagnostic timeline does **not** change the existing Firecloud Core weights or GO / CONDITIONAL GO / NO-GO thresholds. Non-core checkpoints are displayed as `DIAGNOSTIC ONLY` and cannot win the selected operational candidate.

Chronological order is naturally reversed by event geometry:

- Sunset: 0 → −0.5 → −1 → −2 → −3 → −4 → −5 → −6°
- Sunrise: −6 → −5 → −4 → −3 → −2 → −1 → −0.5 → 0°

## V8.0.2 geometry integration

The full 0° to −6° timeline is now connected directly to:

- **Earth Shadow:** shadow-top altitude at every sampled surface distance.
- **Dynamic REZ:** first surface distance toward the Sun where a selected cloud altitude becomes geometrically illuminated.
- **Canvas Illumination Matrix:** 0 / −0.5 / −1 / −2 / −3 / −4 / −5 / −6° × 0–440 km × 2 / 4 / 5 / 8 / 12 / 18 km cloud-altitude state.

The Dynamic REZ is intentionally kept separate from the fixed Operational 350–440 km REZ band. One is a moving geometric illumination boundary; the other is an operational cloud-obstruction diagnostic region.


## V8.0.3 forecast voxel × illumination integration

The geometric illumination lattice is now overlaid with the forecast cloud fields at every civil-twilight checkpoint, direction, distance, and diagnostic altitude. The new matrix spans:

- solar altitude: 0 / −0.5 / −1 / −2 / −3 / −4 / −5 / −6°
- direction: center / ±5°
- surface distance: 0–440 km at the configured route spacing
- diagnostic altitude: 2 / 4 / 5 / 8 / 12 / 18 km

For each cell the engine reports:

- forecast cloud-cover fraction
- geometric Earth-shadow state
- Earth-shadow top altitude and clearance
- upstream cloud-transmission proxy
- path-data completeness
- illuminated fraction of the forecast cloud proxy
- effective illuminated-cloud proxy
- an explicit voxel state (`NO_FORECAST_CLOUD`, `CLOUD_EARTH_SHADOWED`, `SUNLIT_FORECAST_CLOUD`, `SUNLIT_PATH_UNKNOWN`, `MISSING_CLOUD_FORECAST`, or `NO_VERTICAL_FORECAST_SUPPORT`)

The diagnostic quantity is:

`effective illuminated cloud proxy = forecast cloud-cover fraction × geometric sunlit state × upstream transmission proxy`

The target cell is excluded from the new upstream-transmission diagnostic so the target cloud-cover field is not counted twice. This is intentionally separate from the legacy operational path proxy and therefore does not silently change the Firecloud Core score.

### Vertical-data limitation

The current Open-Meteo source exposes coarse low/mid/high cloud-cover fields, not true cloud base/top/thickness voxels. V8.0.3 therefore maps those real forecast fields onto diagnostic altitude checkpoints as **coarse forecast-voxel occupancy proxies**. Heights outside the configured vertical support (currently 18 km) are preserved as Missing (`NO_VERTICAL_FORECAST_SUPPORT`) rather than assumed clear. A future provider with pressure-level cloud water/COT/cloud-base-top data can replace this adapter without changing the illumination matrix interface.

The CASE archive now includes `forecast_voxel_illumination.csv`.

## Current physics layers

- Spherical-Earth shadow geometry `h_min(d, alpha)`
- 0–40 km Primary Canvas
- 40–100 km Extended Canvas
- 100–300 km Corridor
- 300–350 km Strong Blocking diagnostic
- 350–440 km REZ diagnostic
- Center / ±5° direction sampling
- Sun-plane ray cross-section
- Geometric illumination separated from cloud obstruction
- Missing data kept as Missing
- Physical Potential, Visual Magnitude, and Operational Decision shown separately
- CASE ZIP archive

## Important scientific boundary

The current Open-Meteo provider supplies low/mid/high cloud cover, not true cloud optical thickness, cloud base/top voxel geometry, particle phase, particle radius, aerosol vertical profile, or full radiative transfer. Therefore the path transmission term remains an empirical cloud-obstruction proxy and must not be interpreted as physical 600–750 nm transmission.

Atmospheric refraction is not yet folded into the spherical Earth-shadow geometry. The 0° checkpoint is therefore the **geometric** solar-center horizon crossing used by this PhysicsCore.

## Planned physical extensions

1. COT/COD and cloud phase
2. Cloud base/top/thickness and 3-D voxels
3. AOD and aerosol vertical profile
4. HITRAN gas absorption
5. Refraction ray bending
6. Sun–Cloud–Observer scattering angle
7. Multiple scattering
8. Cloud-motion vectors and vertical wind shear
9. Himawari observation mode for present/retrospective analysis only
10. Forecast uncertainty / multi-model ensemble

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Tests

```bash
pytest -q
```

## Deployment status

This package is runnable as a standalone reference build. It is **not labeled as a full replacement** for an existing Taiwan Firecloud production deployment because the current production source tree was not supplied for merge/regression testing.

## V8.0.4 3D cloud-column reconstruction
V8.0.4 adds a 0.5-km vertical voxel lattice and computes Earth-shadow intersection, upstream transmission and effective illuminated cloud-volume proxy. The current Open-Meteo provider only exposes low/mid/high cloud-cover fields, so reconstructed cloud base/top/thickness are coarse layer-envelope proxies rather than native model-level cloud boundaries. Heights without provider support remain Missing.

## V8.1.0 — Pressure-level 3D Cloud Volume & Vertical Optical Blocking

V8.1.0 upgrades the vertical cloud representation from the V8.0.4 low/mid/high envelope proxy to pressure-level cloud profiles. The Open-Meteo provider requests pressure-level cloud cover, relative humidity and geopotential height. Geopotential height is converted from ASL to approximate AGL using model terrain elevation, then interpolated onto the 0.5-km voxel lattice.

The new optical-blocking engine gives every cloud voxel two possible roles:

1. **Target / Canvas** — the cloud voxel itself may be geometrically illuminated.
2. **Upstream Blocker** — the same voxel may attenuate light traveling toward another target voxel.

For each Sun→target ray, the engine evaluates upstream cloud-column intersections and computes an engineering optical-depth proxy:

`tau_proxy = extinction_proxy_per_km × cloud_occupancy × slant_path_length_km`

`T_proxy = exp(-tau_proxy)`

The result is diagnostic and is deliberately **not** called native COD/COT. Open-Meteo pressure-level cloud cover may be native or RH-derived depending on the selected NWP model. Native cloud liquid water, cloud ice, effective radius and spectral optical depth are not yet connected in this standalone reference build.

The operational Firecloud Core score, distance-zone weights and GO/NO-GO thresholds are unchanged in V8.1.0. The new 3D engine is diagnostic-only until calibrated against archived cases and ground truth.

See `說明文件_V8.1.0.md` and `RELEASE_NOTES_V8.1.0.md` for the complete design and limitations.

## V8.1.1 Native 3D Cloud Physics
新增 Native condensate voxel data model：Cloud Liquid Water / Cloud Ice Water / Cloud Fraction / Temperature / RH / Geopotential Height → AGL 3D cloud microphysics。既有 Open-Meteo pressure-level API 無原生 CLWMR/ICMR，因此不會用 RH 假造 condensate；NOAA GFS GRIB2 native adapter contract 已加入，詳見 `說明文件_V8.1.1.md`。

## V8.1.2 — Operational GFS Native GRIB2 pipeline

V8.1.2 closes the data-ingestion gap left in V8.1.1. The application can now request a geographically subsetted NOAA/NCEP GFS 0.25° GRIB2 file from NOMADS for the forecast valid time and route bounding box, decode it with ecCodes, and map native pressure-level fields to every Firecloud route point.

Native fields requested: `CLWMR`, `ICMR`, `TCDC`, `TMP`, `RH`, `HGT`. The provider resolves a likely available GFS cycle, selects the nearest 3-hour forecast lead, caches each run/lead subset, and reuses it across civil-twilight checkpoints. `CLWMR`/`ICMR` are never synthesized from RH. If NOMADS or ecCodes is unavailable, native condensate remains Missing/Unsupported and the existing Open-Meteo profile remains a separate fallback diagnostic.

CASE archives now include `native_gfs_cloud_voxel_3d.csv`, `native_gfs_cloud_columns.csv`, and `native_gfs_provider_metadata.json`.

## V8.1.3 analysis-completion fix
V8.1.3 removes the principal 3-D optical-blocking CPU bottleneck by indexing the vertical cloud field as distance×height arrays instead of repeatedly filtering DataFrames inside every ray segment. Streamlit now reports staged progress and external forecast calls use fail-fast connect/read timeouts. Native GFS download is skipped before network I/O when ecCodes is unavailable. Scientific weights and operational thresholds are unchanged. See `說明文件_V8.1.3.md` and `RELEASE_NOTES_V8.1.3.md`.

---

## V8.1.4 UI state persistence fix

V8.1.4 preserves completed analysis results in `st.session_state` and prevents the CASE ZIP download button from rerunning the Streamlit app (`on_click="ignore"`). Saving a CASE no longer clears the analysis screen. The archived filename is tied to the completed analysis request rather than subsequently edited sidebar values. No physics or scoring logic changed.

## V8.1.5 UI 中文化
V8.1.5 將 Streamlit 主要使用者介面、分析進度、圖表標題／座標、診斷說明與顯示用表格欄名改為繁體中文。內部變數與 CASE CSV 欄位仍維持英文，以確保既有程式與案例封存相容。科學模型與評分門檻未更動。


## V8.2.0 Native Cloud Optical Physics

V8.2.0 adds a microphysics-based cloud optical diagnostic when NOAA GFS native CLWMR/ICMR is available. Native condensate is converted to LWC/IWC, then visible-band extinction is estimated with the geometric-optics relation `beta_ext = 3 Qext M / (4 rho r_eff)` using explicit assumed effective radii (liquid 10 µm, ice 30 µm; Qext≈2). Each 0.5-km voxel receives an estimated vertical COD, while Sun→target ray tracing accumulates slant COD and Beer–Lambert transmission through upstream vertical cloud columns.

This is deliberately labeled a **microphysics-based COD estimate**, not native/retrieved COT. GFS does not provide the effective particle radii used here, so the assumptions are exported with every voxel. Missing CLWMR/ICMR remains Missing. The older pressure-level cloud-cover optical proxy is retained only as a fallback diagnostic and still does not alter the operational Final Score.

New CASE outputs: `native_cloud_optical_blocking_voxel_3d.csv` and `native_cloud_optical_blocking_columns.csv`.

## V8.3.0 — 600–750 nm Spectral RT
新增 600/650/700/750 nm Rayleigh + aerosol Ångström + Native Cloud COD 的 partial spectral transmission。O3/O2/H2O 尚未接 HITRAN/MT_CKD 時保持 Missing；詳見 `說明文件_V8.3.0.md` 與 `RELEASE_NOTES_V8.3.0.md`。

## V8.3.1 — Real Aerosol Forecast
V8.3.1 removes the fixed runtime AOD550 assumption and fetches route-resolved CAMS 550-nm aerosol optical depth through Open-Meteo Air Quality. Missing AOD stays Missing. A real Angstrom exponent is not yet available from this provider, so spectral aerosol scaling is deliberately Missing rather than silently assuming 1.30. CASE archives include the raw route aerosol forecast.

## V8.3.2 — Multi-Wavelength Aerosol Path Physics
V8.3.2 introduces route-resolved aerosol path integration for the 600–750 nm spectral branch. Real multi-wavelength column AOD inputs (550/645/670/800 nm when available) are locally converted to 600/650/700/750 nm by log-log interpolation, without imposing a fixed global Ångström exponent. The model explicitly forbids summing total-column AOD values across the 0–440 km corridor. Instead, each local column AOD is converted to a normalized exponential vertical extinction profile and integrated segment-by-segment along the 3-D observer-to-target ray. This vertical-profile reconstruction is explicitly labelled as an engineering assumption until native CAMS model-level aerosol extinction is connected. If only the Open-Meteo 550 nm AOD is available, spectral aerosol transmission remains Missing.

## V8.3.3 — Native CAMS 3-D Aerosol Extinction
V8.3.3 adds an optional, credential-gated CAMS Global Atmospheric Composition Forecast provider for native pressure-level aerosol extinction coefficient at 532 nm. When ADS API access is configured, the program retrieves a route subset around the Center/±5° 0–440 km domain, decodes the 3-D extinction field with ecCodes, retrieves CAMS multi-wavelength total AOD (550/645/670/800 nm), and uses the real spectral AOD ratios to scale the native 532-nm vertical extinction profile to 600/650/700/750 nm.

The incoming solar aerosol path is now explicitly **Sun→Canvas**, not observer→Canvas. For each Canvas voxel, the model samples route points farther toward the Sun, evaluates the curved-Earth solar-ray altitude, interpolates the native CAMS extinction profile at that altitude, and integrates segment optical depth. If the 0–440 km route terminates before the ray rises above the configured 30-km aerosol-atmosphere top, the result is marked `ROUTE_DOMAIN_TRUNCATED` rather than treated as complete.

The V8.3.2 column-AOD→2-km exponential-profile reconstruction is retained only as a separately labelled fallback diagnostic. Native CAMS failure, missing credentials, missing spectral AOD, or unsupported vertical levels remain Missing. No fixed aerosol climatology or fixed Ångström exponent is substituted.

CAMS ADS access requires API credentials (normally `~/.cdsapirc`) and the `cdsapi` package. This optional provider does not change Final Score or GO/NO-GO thresholds.

## V8.4.0 — HITRAN Gas Spectral RT Foundation
新增本地 HITRAN/HAPI gas RT contract 與 pressure-level T/P/RH gas profile。O₃ 或 HITRAN 資料缺失時 Full Spectral RT 維持 Missing；不使用固定 gas 扣分假設。詳見 `RELEASE_NOTES_V8.4.0.md` 與 `說明文件_V8.4.0.md`。

## V8.4.0.1 hotfix
Fixes an Open-Meteo pressure-level temperature unit mismatch (°C vs K) that could trigger `OverflowError: math range error` in gas RT and distort thermodynamic density calculations. Live Open-Meteo temperatures are now normalized to Kelvin at ingestion; legacy Celsius CASE/cache values are defensively converted in gas RT. Invalid values fail closed to Missing.

## V8.4.0.2 performance hotfix
- Fixes long apparent stall at `0.0° (1/8)` seen in V8.3.3/V8.4.0.
- Prefetches/caches GFS and CAMS provider I/O before the angle loop.
- Adds sub-stage progress within every twilight checkpoint.
- Pre-indexes route aerosol arrays and CAMS vertical profiles; removes repeated Pandas filtering inside voxel ray loops.
- No scoring or scientific threshold changes.


## V8.4.0.3 aggregation hotfix
- Fixes `NameError: gas_profile_frames is not defined` at final result aggregation.
- Initializes the gas-profile frame accumulator before appending per-angle gas profiles.
- Keeps gas profile CASE export intact.
- No scientific or scoring changes.

## V8.4.0.4 — Physics Data Completeness Audit
- `data_completeness` 明確改稱基礎預報／雲場完整率。
- 新增五層 Physics readiness audit：Forecast/Cloud、Native Aerosol、Gas Profile、HITRAN Spectroscopy、Full Spectral RT。
- Missing ≠ Zero ≠ Blocked；未設定 CAMS/HITRAN 不再被誤讀為完整物理鏈。
- CASE 新增 `physics_data_completeness.csv`。

## V8.4.0.6 — 3D Cloud Stage Diagnostics
將原本單一「建立 3D 雲體」進度拆成四個可辨識子階段，便於定位特定太陽高度角的效能瓶頸；科學計算不變。

## V8.4.0.6 — Shared 3D State / Performance Refactor
- coarse cloud upstream ray 改用預索引 NumPy kernel。
- GFS native cloud volume 依 run/lead 共用快取。
- UI/CASE 加入 stage timing 與 cache hit/miss。
- CASE 新增 `performance_diagnostics.csv`。
- 不修改任何科學權重、公式與決策門檻。

## V8.4.0.7 — Optical Blocking Vectorization + End-to-End Wall-clock Audit
- 向量化 pressure-profile cloud proxy 與 native microphysical cloud 的 Sun→Canvas ray integration。
- GFS native optical base 依 run/lead 共用快取。
- `performance_diagnostics.csv` 補齊 provider、每角度、彙整、TOTAL analysis 與 CASE export wall-clock。
- 不修改任何物理公式、權重、閘門或評分。
- 63/63 tests passed。


## V8.4.1 — Real O₃ Atmospheric Profile
- CAMS Global Atmospheric Composition Forecast `ozone` pressure-level mass mixing ratio（kg/kg）接入 Gas Profile。
- O₃ 與既有 CAMS aerosol/geopotential 共用 run/lead/route subset，避免第二次 ADS download。
- CAMS native pressure level 優先；缺少的中間 gas-grid level 只在真實 O₃ levels 之間做 log-pressure interpolation，不外推。
- 輸出 O₃ mass mixing ratio、mole fraction、number density 與 quality/evidence。
- 禁止固定 300 DU、人工標準 O₃ profile、total-column→3D profile 重建。
- Completeness Audit 新增 `O3_PROFILE`；O₃ 完整時 Gas Profile 可轉為 READY，但 Full Spectral RT 仍等待 V8.4.2.1 HITRAN spectroscopy。
- CASE 新增 `ozone_profile_route_snapshots.csv` 與 `cams_native_ozone_provider_status.json`。
- 不修改任何評分、權重、閘門或出勤判定。
- 67/67 tests passed。

## V8.4.1.1 — Streamlit Cloud CAMS ADS credentials
For cloud deployment, set the ADS personal access token in Streamlit Secrets instead of committing `.cdsapirc`. See `說明文件_V8.4.1.1.md`. The provider explicitly constructs `cdsapi.Client(url=..., key=...)`; tokens are never archived in CASE output.

## V8.4.1.2 — CAMS decode audit / O₃ decoupling
CAMS O₃ and 532-nm aerosol extinction now have independent decode outcomes. CASE archives include `cams_grib_message_inventory.csv` so real ADS GRIB identifiers can be audited without exposing credentials. Unknown aerosol encodings remain Missing rather than being guessed.


## V8.4.1.3 — CAMS independent request contracts

CAMS O3, native 532-nm aerosol extinction, and total-column spectral AOD are fetched independently. Official CDS/API variable names are used and CASE archives include `cams_request_audit.csv`.

## V8.4.2.1 — HITRAN 600–750 nm 3D Gas RT
V8.4.2.1 completes the route-resolved incoming Sun→Canvas gas integrator for O2/H2O/O3. It consumes only local HITRAN-derived spectroscopy and the real forecast/CAMS gas profile. No spectroscopy is bundled or fabricated. See `說明文件_V8.4.2.1.md` and `RELEASE_NOTES_V8.4.2.1.md`.

## V8.4.2.2 — CAMS Persistent Cache + Retrieval Grace Window
CAMS ADS retrieval now uses a deterministic persistent cache (`~/.cache/taiwan_firecloud/cams` by default), SHA-256 cache keys stable across processes, cache-first reuse, and a 90-second cold-cache grace window. `FIRECLOUD_CAMS_CACHE_DIR` and `FIRECLOUD_CAMS_DEADLINE_SECONDS` can override deployment settings. Missing/timeout is never converted to zero. See `說明文件_V8.4.2.2.md` and `RELEASE_NOTES_V8.4.2.2.md`.

## V8.4.3.1 — HITRAN Local Spectroscopy Readiness & Deployment Bridge
- `firecloud/hitran_readiness.py` now audits the actual runtime LUT, not just whether a directory exists.
- Runtime spectroscopy becomes READY only when all 12 required gas×wavelength pairs exist: H2O/O3/O2 × 600/650/700/750 nm with finite HITRAN-derived coefficients.
- HAPI is treated as a **build-time** dependency; once the validated local LUT exists, runtime Full Spectral RT does not need to contact HITRAN or import HAPI.
- Supports `HITRAN_API_KEY` and `FIRECLOUD_HITRAN_DB` from environment or Streamlit Secrets (`[hitran] api_key=...`, `db_path=...`) without archiving secret values.
- `bootstrap_hitran_local_db.py` can audit the local database and optionally use an installed HAPI2 builder environment to fetch the required narrow 600–750 nm H2O/O3/O2 transition range.
- `build_hitran_band_coefficients.py` now fails closed on missing local source tables, writes a T/P LUT plus SHA-256 manifest, and never invents spectroscopy.
- Optional one-time HAPI2 builder dependency is isolated in `requirements-hitran-builder.txt`; it is not required by normal Streamlit runtime.
- No firecloud scoring weights, REZ/Canvas geometry, CAMS physics, cloud optics, or decision thresholds changed.

## V8.4.3.1 — HITRAN In-App Bootstrap

V8.4.3.1 adds a one-click Streamlit bootstrap for the remaining local spectroscopy dependency. When a private `HITRAN_API_KEY` is available through Streamlit Secrets, the sidebar can download local H2O/O3/O2 600–750 nm transition tables with HAPI2, build the Firecloud 600/650/700/750 nm temperature/pressure coefficient LUT, and run readiness validation. The API key is passed only through the process environment and is never written to CASE archives or diagnostic logs.

The deployment pins `hitran-api2==0.2.2`, the current PyPI HAPI2 package used for the one-time download step. Runtime Full Spectral RT still consumes only the local HITRAN-derived LUT; missing/incomplete spectroscopy remains Missing rather than zero.


## V8.4.3.2 HITRAN bootstrap stall hotfix
HITRAN one-click bootstrap is now split into H₂O/O₃/O₂ subprocesses with live elapsed-time reporting and hard process-tree deadlines. See `RELEASE_NOTES_V8.4.3.2.md`.


## V8.4.3.3 HITRAN HAPI1 line-download fallback
The deployed HAPI2 0.2.2 transitions workflow reached HITRANonline but returned HTTP 404 while fetching the transitions header for O3. V8.4.3.3 therefore uses official HAPI 1.3 `fetch_by_ids()` as the primary line-by-line downloader and writes HAPI-native `.data/.header` tables directly into `FIRECLOUD_HITRAN_DB`. Existing complete gas tables are cache hits. HAPI2 is disabled as an automatic fallback by default and can only be re-enabled explicitly with `FIRECLOUD_HITRAN_ALLOW_HAPI2_FALLBACK=1`.

Natural-isotopologue global IDs used by the downloader are H2O `[1,2,3,4,5,6,129]`, O3 `[16,17,18,19,20]`, and O2 `[36,37,38]`. No line data or API key are bundled into the deployment package.


## V8.4.3.4 HITRAN remote 404 fallback
若 HAPI/HAPI2 transitions remote endpoint 在部署環境回 404，使用者可由 HITRANonline Line-by-Line Search 下載標準 `.par` 檔並在 App 內匯入。匯入器驗證 gas molecule ID 與 600–750 nm 範圍，然後建立 HAPI-native `.data/.header`。三個 gas table 齊全後可只執行 288-state LUT，不需再次觸發 remote fetch。

## V8.4.4 HITRAN Offline Runtime LUT Workflow

正式部署不再要求每次 Streamlit 啟動時下載 HITRAN raw line data。建議一次性建立並保存衍生的 288-state Runtime LUT，再由 `hitran_runtime/` 或 `FIRECLOUD_HITRAN_LUT_PATH` 載入。

Runtime 嚴格網格為 3 gases × 4 wavelengths × 4 temperatures × 6 pressures = 288 states。程式提供 LUT CSV/manifest 匯入、驗證、安裝與下載保存功能。Remote HAPI download 僅保留 Legacy 診斷用途。


## V8.4.4.1 HITRAN Offline-Only Workflow Hotfix

正式 UI 不再主動引導 HAPI remote bootstrap。H₂O/O₃/O₂ line tables 未齊全時 LUT Build 按鈕停用；Legacy remote download 僅在進階區明確 opt-in 後可執行。Runtime LUT CSV + manifest 可跨地點、跨國家、跨後續版本沿用。

## V8.4.5 Hybrid Gas Spectroscopy

V8.4.5 corrects the visible-band gas spectroscopy model for 600–750 nm:

- H2O: HITRAN standard line list + HAPI Voigt diagnostic-band coefficients.
- O2: HITRAN standard line list + HAPI Voigt diagnostic-band coefficients.
- O3: Serdyuchenko–Gorshelev temperature-dependent absorption cross sections, not a nonexistent visible HITRAN line table.
- Runtime remains LUT-only. Raw spectroscopy inputs are build-time files and are not redistributed in the deploy ZIP.
- Hybrid Runtime LUT remains 288 rows: 3 gases × 4 diagnostic wavelengths × 4 temperatures × 6 pressures.
- V8.4.5 temperature nodes are 220 / 250 / 280 / 293 K. The former 300 K node is replaced by 293 K because the O3 experimental XSC ends at 293 K; no O3 temperature extrapolation is allowed.
- O3 XSC is linearly interpolated only between measured 193–293 K spectra and band-averaged over the same ±12.5 nm diagnostic bands used for H2O/O2.
- Runtime validation now requires hybrid provenance: H2O/O2 must be HITRAN-derived and O3 must be Serdyuchenko–Gorshelev-derived.

### Build-time inputs

Upload/import these three sources in the Streamlit HITRAN/Hybrid Gas Spectroscopy panel:

1. H2O 600–750 nm standard HITRAN `.par` line list.
2. O2 600–750 nm standard HITRAN `.par` line list.
3. `SerdyuchenkoGorshelev5digits_latest.dat` O3 absorption cross-section dataset.

After all three are READY, build and save the derived Runtime LUT CSV + manifest. The saved Runtime LUT can be reused for any observation location, including outside Taiwan.


## V8.4.5.2 Manual HITRAN import hotfix

- Fixes `NameError: NUMMAX is not defined` in the manual HITRAN `.par` validation/import path.
- The correct constant is `NUMAX`; both error/reporting branches now use the same defined upper wavenumber bound.
- Python 3.14 HAPI `SyntaxWarning` messages shown during import are upstream warnings and are not the cause of the import failure.
- No scientific weights, spectroscopy source choices, or decision thresholds are changed.


## V8.4.5.2 LUT builder performance
Hybrid LUT 建表改為每個 gas/T/P 只呼叫一次完整 600–750 nm Voigt spectrum，四個 25 nm bands 共用該 spectrum；HAPI calls 192→48。


## V8.4.6 Embedded Runtime Spectroscopy + route interpolation performance

- Packages the verified 288-state Hybrid Gas Spectroscopy Runtime LUT in `hitran_runtime/`.
- Runtime resolution prefers the packaged LUT, so normal deployments no longer need to upload H2O/O2/O3 source spectra or rebuild the LUT.
- Replaces per-point pandas route interpolation with a vectorized two-time-slice interpolation and precomputes all 8 twilight snapshots before the angle loop.
- Adds `OPENMETEO_ROUTE_INTERPOLATION` performance diagnostics and a separate GFS merge progress checkpoint.
- No firecloud score weights, decision thresholds, cloud physics, gas spectroscopy coefficients, or missing-data semantics are changed.

## V8.4.7.3 API request audit
Open-Meteo forecast now uses exact-coordinate de-duplication plus deterministic persistent batch caching. Open-Meteo Air Quality AOD550 is fallback-only when native CAMS aerosol data are incomplete. CASE archives include Open-Meteo request audit CSVs.

## V8.4.8 Shared-Column Spectral RT
V8.4.8 vectorizes the dominant Hybrid gas RT hot loop. Vertical cloud targets at one direction/distance share route segments and are solved together. This is a performance-only change: Dynamic REZ, the extended domain, spectroscopy, cloud physics, gates, and scores are unchanged.


## V8.4.9 Physics-Terminated Dynamic RT Domain

V8.4.9 removes the fixed 840 km Dynamic RT boundary as a scientific termination rule.
The provider route is now sized from spherical ray geometry so that every directly-sunlit
0–100 km Canvas target in the configured 0°…−6° timeline can reach the configured
0–18 km PhysicsCore model ceiling. With the default configuration this derives a 1040 km
provider route. The number is an output of the geometry, not a fixed REZ constant.

Within gas RT, every individual Sun→cloud ray terminates when it exits the real
pressure-profile-supported model domain. Earth-shadowed voxels are explicitly N/A rather
than Missing. True failure causes are separated into target-above-profile, missing vertical
bracket, missing route sample, and Dynamic route exhaustion. No gas is fabricated above
the highest real pressure level.

Operational FULL_SPECTRAL_RT completeness is now scoped to directly-sunlit 0–100 km
Canvas targets. All-route RT remains separately reported as
FULL_SPECTRAL_RT_ALL_ROUTE_DIAGNOSTIC, so far-route REZ/blocker diagnostics cannot
artificially lower the operational completeness metric. GAS_VERTICAL_DOMAIN is also
reported separately; the current real pressure-level top remains an explicit scientific
limitation rather than being hidden by extrapolation.

## V8.4.9.3 UI continuity
即使所有核心候選因資料完整率 gate 被排除，分析完成後仍會完整顯示診斷層與 CASE 下載；正式 operational selection 仍維持 N/A，不以診斷角度冒充正式候選。


## V8.4.10 CAMS operational-cycle availability

CAMS 00/12 UTC cycle selection now follows the provider delivery window (default 10.25 h safety lag) instead of the earlier 8 h assumption. This prevents current-day ADS 400 invalid-combination failures before the newest cycle is published.

## V8.4.10.1 Full RT integrity gate

V8.4.10.1 makes the operational spectral completeness gate path-aware. The Dynamic provider/RT route now continues until directly sunlit Canvas rays reach the 30 km CAMS aerosol atmosphere-top checkpoint, while the cloud target domain remains 0–18 km. Gas and aerosol partial-path values remain auditable but cannot be counted as complete Full Spectral RT. A bounded role-specific retry is added only for failed CAMS spectral-column AOD requests; successful aerosol/O3 roles are never re-requested.

## V8.4.10.2 CAMS conservative serial scheduler

V8.4.10.2 changes CAMS provider execution from three simultaneous ADS roles per Dynamic tile to a conservative serial, process-isolated scheduler. This is a reliability/completeness change, not a scientific-weight or performance optimization. Successful CAMS roles are never re-requested. Prompt retryable failures may retry once with bounded backoff, while `TIMEOUT_DEFERRED` is not immediately duplicated because the remote ADS job may still exist after the local worker is terminated. A cooldown is inserted after timeouts before the next ADS role is submitted. Audit rows include `scheduler_mode`, retry metadata, and timeout state.


## V8.4.10.3 CAMS child watchdog / heartbeat

Adds CAMS worker heartbeats, hard child-process reaping after every role, and fail-fast handling when a child exits without a result. No scientific weights or provider request contracts are changed.

## V8.4.10.4 CAMS file-backed IPC watchdog

CAMS isolated child 不再使用 `multiprocessing.Queue` 傳輸大型 pandas DataFrame。每個 child 將結果原子寫入暫存 pickle，parent 只以 process liveness + heartbeat 管理 90 秒 deadline。這避免 Queue pipe 在大型 payload 傳輸期間讓主程序卡在 `recv_bytes()/unpickle`，使 watchdog 失效。Retry 狀態也改為獨立顯示，避免原始 role 的 FAILED 被重試 RUNNING 覆蓋。

## V8.4.10.5 External CAMS worker + persistent session recovery

CAMS provider isolation no longer uses Python `multiprocessing.spawn` from the Streamlit process. Each role is executed by a dedicated `python -m firecloud.providers.cams_worker` subprocess with JSON request + atomic file-backed result IPC, 5-second heartbeat polling, and a 90-second hard process-group deadline. This keeps the worker independent from `app.py` and reduces the risk that CAMS isolation destabilizes the Streamlit main process.

The app also maintains `.firecloud_state/analysis_job_state.json` and a last-completed-result pickle. If a Streamlit session/process is interrupted, the original event settings and last progress are restored and the UI offers to continue the interrupted analysis using provider caches instead of returning to an unexplained blank initial state.
# Taiwan Firecloud PhysicsCore V8.4.16.7

## V8.4.16.7 — native cloud canvas and blocker role diagnostics

Native cloud optical output now separates the role of a condensate-missing
target from an unknown upstream blocker path. It records whether a target cloud
is on a sunlit path, whether the target can be credited as an effective canvas,
and the fraction of the upstream path whose native extinction is unknown. These
diagnostics never convert missing condensate to zero or fabricate COD.

## V8.4.16.6 — route endpoint diagnostics for cloud optical blocking

This release marks the terminal voxel of each finite Sun-to-target route as
`ROUTE_ENDPOINT_NO_UPSTREAM_CHECK`. It no longer reports an empty upstream
path as fabricated 100% transmission or credits that voxel as an effective
illuminated cloud volume. Transmission and path completeness are NaN at the
endpoint, while the chart adds an explicit endpoint marker. This is a domain
boundary diagnostic, not a claim that the endpoint is cloudy or clear.

## V8.4.16.5 — bounded CAMS prefetch and RT boundary diagnostics

The analysis deduplicates identical CAMS run/lead keys and now prefetches up to
two different time bundles concurrently. The three roles inside each bundle
remain serial to protect the ADS queue. Use
`FIRECLOUD_CAMS_PREFETCH_WORKERS=1` when a deployment needs fully serial ADS
scheduling.

RT reports model-top and model-bottom finite-domain terminations separately from
true missing data, uses a small pressure-profile boundary tolerance, and
excludes Earth-shadow N/A rows from applicable all-route completeness. CASE
archives include per-worker CAMS checkpoint evidence.

V8.4.15 keeps the V8.4.14 durable worker/recovery architecture and adds
pressure-profile boundary clipping for gas RT. A ray segment that crosses the
real profile top or bottom is integrated only over its supported fraction; no
vertical extrapolation is introduced. CASE output now includes O3-only
transmission diagnostics, layered spectral missing causes, boundary-clipping
flags, and the CAMS worker checkpoint. CASE ZIP compression uses a low CPU
level to reduce export wall time without changing scientific values.

The 575 nm band is supported by the LUT builder through `--wavelengths
575,600,650,700,750`, but it is not enabled in the packaged runtime LUT in
this release because the uploaded source did not contain verifiable local
H2O/O2 line tables and O3 cross-section data for that band. The builder fails
closed until those real inputs are supplied; it never interpolates 575 nm from
another band.

## V8.4.16 — validated 575 nm extension

V8.4.16 adds a fail-closed 575 nm production path. H2O and O2 must come from
real HITRAN line data covering 560–765 nm; O3 uses the supplied
Serdyuchenko–Gorshelev temperature-dependent XSC. The complete derived table
contains 360 states (3 gases × 5 wavelengths × 4 temperatures × 6 pressures).
575 nm is enabled only after all three gases pass the complete 24-state
575-nm grid check. Existing 600/650/700/750 nm Runtime behavior remains intact
when the extended source data are missing. See `說明文件_V8.4.16.md` and
`RELEASE_NOTES_V8.4.16.md`.

## V8.4.16.1 — O₃ XSC build-source hotfix

The supplied and validated Serdyuchenko–Gorshelev XSC is included under
`spectroscopy_sources/` and is automatically selected by the Streamlit LUT
builder when the user has not separately imported it into `FIRECLOUD_HITRAN_DB`.
This fixes the case where H₂O/O₂ downloads completed but LUT creation stopped
with `O3_XSC` missing. H₂O/O₂ line lists remain build-time local data and still
come from the 560–765 nm HITRAN download/import path.

## V8.4.16.2 — sparse HITRAN O₂ coverage correction

Manual `.par` validation now checks real transitions in each diagnostic band
instead of requiring global line-list endpoints to touch 560/765 nm. This is
important for sparse O₂ data: the supplied 575-nm band has real transitions,
while the 600-nm band may be a valid physical gap. Missing data are still not
converted to zero, and H₂O/O₂/HITRAN plus the existing four-band fallback rules
are preserved.

## V8.4.16.3 — resumable hybrid LUT build

The H₂O/O₂ Voigt builder writes an atomic checkpoint after each completed
temperature-pressure state and resumes only when the input/grid signature
still matches. A 600-second hard timeout no longer discards already completed
states. The default parent-process deadline is now 3600 seconds, configurable
through `FIRECLOUD_HITRAN_LUT_TIMEOUT_SECONDS` within 60–7200 seconds. The
scientific grid and `0.02 cm⁻¹` default resolution are unchanged. See
`說明文件_V8.4.16.3.md` and `RELEASE_NOTES_V8.4.16.3.md`.

## V8.4.16.4 — completed-job reconciliation and packaged 360-state LUT

The app reconciles the persisted analysis journal with the worker progress file
on page load. If the worker already wrote COMPLETED and its atomic result exists,
the stale interrupted-analysis banner is cleared automatically. HAPI 1.3
legacy `SyntaxWarning` output is also suppressed during diagnostic imports;
calculation errors remain visible.

The verified 360-state 575/600/650/700/750 nm derived LUT is packaged under
`hitran_runtime/` and can be reused without HAPI or the raw HITRAN line lists.
See `說明文件_V8.4.16.4.md` and `RELEASE_NOTES_V8.4.16.4.md`.

See `說明文件_V8.4.16.7.md`, `RELEASE_NOTES_V8.4.16.7.md`, and the prior
V8.4.16.5 notes.

## Active V1.0 documentation
- `RELEASE_NOTES_PhysicsCore_V1.0-R2.1.md` — current R2 release notes.
- `RELEASE_NOTES_PhysicsCore_V1.0-R1.md` — previous V1.0 checkpoint notes.
- `V1.0_MIGRATION_FROM_V8.md` — concise historical migration record; individual V8.x release-note files are intentionally excluded from this package.
