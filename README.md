
## PhysicsCore V1.0-R4.9.1 — Target Canvas Optics + Packaged Six-Band LUT

R4.9.1 keeps the R4.9 target-cloud optical evidence resolver and packages the validated 432-row six-band gas spectroscopy Runtime LUT (550/575/600/650/700/750 nm) so deployment is READY without rebuilding HITRAN coefficients. It never converts Cloud Fraction or RH into COT. CASE exports now include `v1_target_canvas_optical_evidence.csv` and `v1_target_canvas_optical_summary.csv`.

# Taiwan Firecloud PhysicsCore V1.0

**Current checkpoint: V1.0-R4.8.2 — Incremental 550 nm LUT Builder.**

R4.8.2 accelerates six-band spectroscopy completion by strictly reusing the validated 360-row 575–750 nm derived Runtime LUT and calculating only the missing 550 nm H2O/O2/O3 states (72 rows), then merging and validating the final 432-row LUT. 550 nm is still calculated from real local spectroscopy and is never interpolated from 575/600 nm.


R4.5.1 fixes the provider-to-CloudScene condensate schema bridge identified by the R4.5 CASE audit. ecCodes emits `cloud_liquid_water_kgkg_<p>hPa` / `cloud_ice_water_kgkg_<p>hPa`; native cloud reconstruction now consumes that canonical kg/kg contract directly. Older CASE/replay aliases without `_kgkg_` are accepted only as compatibility input and normalized to the canonical names.

R4.5 hardens the GFS native-cloud data chain so CLWMR/ICMR cannot silently disappear behind a generic provider `OK` state. The GFS cache is request-schema aware, cached/downloaded GRIB files are inventoried with ecCodes, required condensate fields are validated, invalid caches are rejected and redownloaded, and CASE archives retain detailed GFS request/inventory/completeness diagnostics.

Frozen physics behavior remains unchanged: Missing is not Clear or Zero; cloud geometry never substitutes for cloud optical evidence; RH/cloud fraction/base/top do not fabricate COT/COD.

See `RELEASE_NOTES_PhysicsCore_V1.0-R4.8.2.md` and `IMPLEMENTATION_STATUS_PhysicsCore_V1.0-R4.8.2.md`.

## R5.1 Secondary Target Optical Evidence
R5.1 adds a provider-neutral forecast-only secondary Target Canvas optical contract. Multi-source disagreements remain explicit and are never averaged away. No satellite observation is used as future forecast input.


## R5.1 ECMWF IFS secondary cloud optics
Set `FIRECLOUD_ECMWF_IFS_GRIB_PATH` to an entitled/mounted IFS model-level forecast GRIB containing CLWC/CIWC/CC/T/Q plus hybrid coefficients and surface pressure/geopotential. Missing access remains explicit Missing.


## R5.2 finite-solar-disk penumbra
R5.2 exports H_any_sun / H_solar_center / H_full_solar_disk and actual F_sun + 650/700/750 nm Sun-to-CloudBase evidence. The traditional Earth-shadow height is diagnostic only; the transition zone is explicitly retained.
