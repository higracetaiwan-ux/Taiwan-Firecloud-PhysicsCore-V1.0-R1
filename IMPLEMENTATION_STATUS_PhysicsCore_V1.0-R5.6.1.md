# PhysicsCore V1.0-R5.6.1 Implementation Status

## Completed
- Projected adjacent-node Cloud→Observer cloud-volume geometry.
- Foreground low-cloud blockers separated from photographic firecloud targets.
- Missing viewing occupancy remains Missing.
- DWD ICON native source-address decoder retained.
- DWD ICON vertical geometry reconstructed from native P/T + forecast surface anchor; no per-level FI dependency.
- Existing upstream secondary optical bridge retained.
- Six-band dataframe fragmentation warning removed.
- Full regression: 283 passed / 0 failed.

## Still deliberately unresolved / future physics
- Full Cloud→Observer six-band spectral extinction (cloud COT, aerosol/haze/fog, precipitation).
- 3D precipitation optical path closure.
- Ground-truth calibrated Viewing obstruction thresholds.
- Ground-truth calibrated photography probability.

These are missing physics capabilities, not R5.6.1 software regressions, and must remain explicit rather than inferred.
