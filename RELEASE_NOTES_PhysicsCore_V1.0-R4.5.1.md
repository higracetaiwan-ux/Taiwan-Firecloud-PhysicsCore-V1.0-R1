# Taiwan Firecloud PhysicsCore V1.0-R4.5.1

## Native Condensate Schema Bridge Fix

- Fixes the R4.5 audit finding that GFS ecCodes decode produced `cloud_liquid_water_kgkg_<p>hPa` / `cloud_ice_water_kgkg_<p>hPa`, while `native_cloud.py` attempted to read legacy names without `_kgkg_`.
- Standardizes the canonical condensate contract on explicit kg/kg field names.
- Keeps legacy no-unit aliases only as CASE/replay compatibility input; they are normalized to canonical names and never become a second physics contract.
- Preserves Missing != Clear != Zero. No RH/cloud-fraction/base/top COT synthesis is introduced.
- Adds regression tests proving canonical CLWMR/ICMR reach `native_levels_from_row()` and `build_native_cloud_volume()` as supported microphysics.
- CASE filename and UI checkpoint labels updated to R4.5.1.
