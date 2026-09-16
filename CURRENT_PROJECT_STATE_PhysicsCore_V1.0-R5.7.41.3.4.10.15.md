# CURRENT PROJECT STATE — Taiwan Firecloud PhysicsCore V1.0

## Current Version
`V1.0-R5.7.41.3.4.10.15`

Status: **IMPLEMENTATION / REGRESSION PASS — FIELD VALIDATION PENDING**

Last FIELD PASS: `V1.0-R5.7.41.3.4.10.14`

Science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`

## Current Milestone
Ice Optics Phase 2 Step 3B — **GFS v16 Exact Scheme Pinning Evidence Gate**

### Pinned
- GFS v16 operational microphysics family = GFDL Cloud Microphysics.
- Public reproduction source path = `physics/MP/GFDL/v1_2019`.
- GFS_v16 CCPP emulation `reiflag=2`.
- `reiflag=2` semantic = cloud-ice effective radius.
- Public `rei` bounds = 10–150 µm.

### Still unresolved / blocked
- NCEP production binary exact commit provenance.
- Yang/Bi Dmax semantic bridge.
- scheme-native PSD reconstruction authorization.
- habit / roughness.
- independent validation.

Therefore:
- `GFSV16_DMAX_MAPPING_ELIGIBLE=false`
- `GFSV16_PSD_RECONSTRUCTION_ELIGIBLE=false`
- `PRODUCTION_ICE_OPTICS_READY=false`
- `physics_promotion_allowed=false`

## Regression
- Targeted: 39/39 PASS
- Full working-tree: 796/796 PASS
- Existing pandas FutureWarning only

## Next
Run a `.10.15` FIELD CASE and verify the 3 new Step 3B artifacts + 3 Analysis Integrity gates + 3 CASE Archive required-member gates.
