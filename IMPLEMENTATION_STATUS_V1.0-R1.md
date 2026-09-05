# PhysicsCore V1.0 R1 implementation checkpoint

Baseline: V8.4.16.7-PhysicsCore
New main-program identity: Taiwan Firecloud PhysicsCore V1.0

## Implemented in R1
- V1 data contracts and no-score PhysicsCoreResult boundary.
- Frozen 0°..-4° half-degree Core Formation angle contract.
- Six-band 550/575/600/650/700/750 nm contract.
- Native-model-level multi-layer cloud segmentation with CLEAR-gap splitting.
- Geometry evidence and optical evidence separation.
- Finite-solar-disk G0 DirectSolarFraction primitive.
- New Streamlit program name/version and V1 CASE filename.

## Compatibility still present
The inherited V8.4.16.7 provider/RT execution path remains operational inside R1 so the package is runnable while the refactor proceeds. Legacy Physics Score / completeness gate / fixed-distance scoring have not yet been removed from that compatibility execution path; they are excluded from the new V1 contracts and will be replaced in subsequent checkpoints.

## Test state
- New R1 focused tests: PASS.
- Full suite: 177 passed, 9 failed. The nine failures match known/stale inherited V8-era expectations (old release strings/LUT row assumptions plus the already-known endpoint native-cloud test) and are not new R1 contract failures.
