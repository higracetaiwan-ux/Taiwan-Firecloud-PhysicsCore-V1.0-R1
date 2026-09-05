# Taiwan Firecloud PhysicsCore V1.0

**Current checkpoint: V1.0-R4.6 — Geometry/Optics Evidence Decoupling.**

R4.6 decouples native cloud geometry/occupancy evidence from native condensate optical evidence. Non-zero native cloud fraction can preserve `PARTIAL_OCCUPANCY` / `CLOUD_OCCUPIED` geometry even when CLWMR/ICMR are zero. Such disagreement is tagged `CF_CLOUD_CONDENSATE_ZERO` and does **not** fabricate COT. Positive condensate with very low cloud fraction is tagged `CONDENSATE_CLOUD_CF_LOW` and also fails closed for trusted COT. Geometry and optics therefore remain independent evidence tracks as required by PhysicsCore V1.0.


R4.5.1 fixes the provider-to-CloudScene condensate schema bridge identified by the R4.5 CASE audit. ecCodes emits `cloud_liquid_water_kgkg_<p>hPa` / `cloud_ice_water_kgkg_<p>hPa`; native cloud reconstruction now consumes that canonical kg/kg contract directly. Older CASE/replay aliases without `_kgkg_` are accepted only as compatibility input and normalized to the canonical names.

R4.5 hardens the GFS native-cloud data chain so CLWMR/ICMR cannot silently disappear behind a generic provider `OK` state. The GFS cache is request-schema aware, cached/downloaded GRIB files are inventoried with ecCodes, required condensate fields are validated, invalid caches are rejected and redownloaded, and CASE archives retain detailed GFS request/inventory/completeness diagnostics.

Frozen physics behavior remains unchanged: Missing is not Clear or Zero; cloud geometry never substitutes for cloud optical evidence; RH/cloud fraction/base/top do not fabricate COT/COD.

See `RELEASE_NOTES_PhysicsCore_V1.0-R4.6.md` and `IMPLEMENTATION_STATUS_PhysicsCore_V1.0-R4.6.md`.
