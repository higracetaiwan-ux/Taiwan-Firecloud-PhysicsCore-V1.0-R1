# Taiwan Firecloud PhysicsCore V1.0-R5.7.2

## Runtime hotfix

- Fixes `ValueError: cannot insert time, already exists` in the R5.7 Viewing spectral route snapshot pipeline.
- `interpolate_route_at_time()` already returns a `time` column; R5.7 attempted to insert the same column again before exporting Viewing route snapshots.
- R5.7.2 updates existing metadata columns in place and only inserts `solar_altitude_deg` when absent, then reorders columns deterministically.
- No Formation, Penumbra Geometry, Sun→CloudBase Spectral RT, target cloud optical response, Viewing physics, or Photography Decision thresholds are changed.
- Adds a regression test covering an interpolated route snapshot that already contains `time`.

## Verification

- Full regression suite: 288 passed / 0 failed.
