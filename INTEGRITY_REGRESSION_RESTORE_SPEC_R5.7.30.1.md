# R5.7.30.1 Integrity Regression Restore Specification

## Scope

R5.7.30.1 does not alter the R5.7.30 Twilight Glow science. It restores the
already field-validated R5.7.29.1 Viewing precipitation integrity contract.

## Required checks

1. `VIEWING_PRECIPITATION_TARGET_COVERAGE` compares eligible Viewing targets
   against precipitation evidence by `time + solar_altitude_deg + canvas_id`.
   Missing or extra keys are hard FAIL.
2. `VIEWING_NATIVE_HYDROMETEOR_HANDOFF` applies when GFS `RWMR`, `SNMR`, and
   `GRLE` are all READY. Full target coverage is required and no row may remain
   `VIEW_PRECIPITATION_VOLUME_UNRESOLVED`.
3. A non-empty table alone is not sufficient evidence.

## Frozen boundaries

Formation, Viewing extinction equations, Twilight Glow, Photography, 13 angles,
six bands, route resolution, provider policy and Missing/Clear/Zero/N/A semantics
are unchanged.
