# Taiwan Firecloud PhysicsCore V1.0

**Current checkpoint: V1.0-R4.8.1 — Incremental 550 nm LUT Builder.**

R4.8.1 accelerates six-band spectroscopy completion by strictly reusing the validated 360-row 575–750 nm derived Runtime LUT and calculating only the missing 550 nm H2O/O2/O3 states (72 rows), then merging and validating the final 432-row LUT. 550 nm is still calculated from real local spectroscopy and is never interpolated from 575/600 nm.


R4.5.1 fixes the provider-to-CloudScene condensate schema bridge identified by the R4.5 CASE audit. ecCodes emits `cloud_liquid_water_kgkg_<p>hPa` / `cloud_ice_water_kgkg_<p>hPa`; native cloud reconstruction now consumes that canonical kg/kg contract directly. Older CASE/replay aliases without `_kgkg_` are accepted only as compatibility input and normalized to the canonical names.

R4.5 hardens the GFS native-cloud data chain so CLWMR/ICMR cannot silently disappear behind a generic provider `OK` state. The GFS cache is request-schema aware, cached/downloaded GRIB files are inventoried with ecCodes, required condensate fields are validated, invalid caches are rejected and redownloaded, and CASE archives retain detailed GFS request/inventory/completeness diagnostics.

Frozen physics behavior remains unchanged: Missing is not Clear or Zero; cloud geometry never substitutes for cloud optical evidence; RH/cloud fraction/base/top do not fabricate COT/COD.

See `RELEASE_NOTES_PhysicsCore_V1.0-R4.8.1.md` and `IMPLEMENTATION_STATUS_PhysicsCore_V1.0-R4.8.1.md`.
