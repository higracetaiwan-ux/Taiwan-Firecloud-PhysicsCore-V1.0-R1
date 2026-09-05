# Taiwan Firecloud PhysicsCore V1.0-R2

## Checkpoint scope

R2 begins the actual runtime transition from the inherited V8 execution semantics to the frozen PhysicsCore V1.0 contracts. It does **not** claim Formation, Viewing, Glow, spectral color, Peak Window or Decision Layer are complete.

## Implemented in R2

- Runtime Core Formation timeline is now the frozen nine-angle grid: `0, -0.5, -1, -1.5, -2, -2.5, -3, -3.5, -4 deg`.
- Added `firecloud/v1_runtime.py` as the V1 runtime bridge.
- Native model-level `CloudScene` is built at each core angle.
- Canvas candidates are created from native cloud layers inside the operational 0-100 km Canvas domain without distance scoring.
- Each Canvas receives its own G0 finite-solar-disk `DirectSolarFraction` state.
- Each Canvas receives its own `Sun->CloudBase` sampled ray.
- Dynamic REZ is represented as ray-derived segment IDs where `F_sun > 0`; no fixed 350-440 km interval defines R2 ray physics.
- Added V1 dependency-aware evidence tables. Missing CAMS/O3/aerosol no longer erases known Cloud Geometry or DirectSolarFraction in the V1 outputs.
- CASE archives now include V1 Core summary, Cloud Layers, Canvas Candidates, DirectSolarFraction, Solar Rays, Solar Geometry and dependency-status CSV files.
- The Streamlit UI now presents V1 R2 geometry/illumination outputs first. Inherited V8 `physics_score`, global completeness and GO/NO-GO are explicitly labeled Legacy diagnostic compatibility fields.

## Deliberate compatibility boundary

The inherited V8 cloud optical, gas, aerosol and spectral RT pipelines remain available in R2 as a compatibility/diagnostic branch while V1 optical-path contracts are connected. Their `physics_score`, `selected_angle`, global minimum completeness and operational decision are **not** PhysicsCore V1 outputs and must not be used as the new architecture's physical truth.

## Next checkpoint

R3: connect actual ray-cloud intersections and six-band dependency-aware OpticalPathResult to the Canvas-specific rays, including cloud/gas/aerosol/precip evidence propagation without a global completeness gate.
