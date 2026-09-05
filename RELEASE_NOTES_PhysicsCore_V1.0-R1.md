# Taiwan Firecloud PhysicsCore V1.0-R1

## New program identity

The main program is renamed **Taiwan Firecloud PhysicsCore V1.0**.  V8.4.16.7 is retained only as the compatibility baseline inside this first refactor checkpoint.

## R1 implemented

- Added the frozen V1.0 Stage-1 data-contract layer (`firecloud/contracts.py`).
- Added six-band contract: 550 / 575 / 600 / 650 / 700 / 750 nm.
- Added frozen 0° to -4° Core Formation angle contract at 0.5° spacing (9 checkpoints).
- Added pre-sunset, late-firecloud and nautical-twilight diagnostic angle contracts.
- Added native-model multi-layer cloud segmentation (`firecloud/cloud_scene.py`). Native CLEAR or UNKNOWN gaps do not silently bridge separated cloud layers.
- Geometry/optical evidence are separated. Cloud fraction occupancy does not fabricate COT/COD.
- Added finite-solar-disk geometric DirectSolarFraction foundation (`direct_solar_fraction_g0`). Legacy Earth-shadow height remains diagnostic.
- Added V1 contract tests ensuring PhysicsCoreResult contains no Final Score / GO-NO-GO / selected-angle leakage.
- Main Streamlit title, version identity and CASE filename now use the new V1.0 program name.

## Deliberate R1 compatibility boundary

The expensive inherited V8 provider/RT scheduler still runs its bounded legacy diagnostic timeline in R1.  The frozen V1 Core 9-angle contract is already present, but the provider/RT scheduler will be switched to dependency-aware V1 execution in the next checkpoints. This prevents R1 from multiplying GFS/CAMS/HITRAN calls before cache/scheduling refactoring is complete.

No claim is made that Formation / Viewing / Glow / Decision refactors are complete in R1.
