# Taiwan Firecloud PhysicsCore V1.0-R4.5

## GFS Native Condensate Provider Validation

R4.5 fixes the provider-validation gap that could leave CLWMR/ICMR absent while the GFS native provider still reported a generic OK state.

### Changes
- GFS GRIB cache identity now includes a request-schema fingerprint covering provider schema version, requested variables, pressure levels, file/run/lead, and bbox.
- Old/incomplete caches can no longer silently satisfy a newer native-condensate request.
- Every cached/downloaded GRIB is inventoried with ecCodes before acceptance.
- CLWMR and ICMR pressure-level messages are explicitly required for native-condensate readiness.
- Cache entries missing required condensate fields are invalidated and redownloaded once.
- Native provider statuses are now explicit, including `FULL_NATIVE_MICROPHYSICS`, `MISSING_REQUIRED_CONDENSATE_FIELDS`, and `CONDENSATE_FIELDS_DECODED_BUT_NO_ROUTE_VALUES`.
- CASE archive adds:
  - `gfs_native_request_audit.csv`
  - `gfs_grib_message_inventory.csv`
  - `gfs_native_field_completeness.csv`
- Provider metadata records CLWMR/ICMR route-value counts and the request schema fingerprint.

### Physics policy preserved
- Missing condensate is never converted to clear sky or zero COT.
- RH/cloud fraction/base/top are not used to fabricate COT/COD.
- Slant cloud RT only activates after genuine native condensate optical evidence exists.

### Tests
- R4.5 provider-validation tests: 3/3 passed.
- Focused GFS/R4.x tests: 12/12 passed before adding R4.5 tests.
- Full suite: 208 passed / 9 known Legacy V8 stale-contract failures.
