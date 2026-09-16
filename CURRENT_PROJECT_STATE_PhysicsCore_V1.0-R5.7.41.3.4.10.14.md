# CURRENT PROJECT STATE — Taiwan Firecloud PhysicsCore V1.0

## Current Version
`V1.0-R5.7.41.3.4.10.14`

Status: **IMPLEMENTATION / REGRESSION PASS — FIELD VALIDATION PENDING**

Last FIELD PASS: `V1.0-R5.7.41.3.4.10.13 FIELD PASS`

Science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`

## Current Milestone
Ice Optics Phase 2 Step 3 — **Global Mapping Candidate Intake + Scheme Contract Qualification**

## Global-first decision
全球 forecast coverage 現在是 mapping candidate 的優先條件，但不是 mapping eligibility 的充分條件。

Primary investigation target:
`NOAA_GFS_V16_GFDL_MP_CURRENT`

原因：
- 全球 operational，涵蓋台灣；
- PhysicsCore 已 ingest GFS native mass fields；
- operational GFS v16 scheme family 已知為 GFDL Cloud Microphysics；
- 但 exact runtime revision/config/PSD parameter set 與 Yang/Bi Dmax semantic bridge 尚未 pin，因此仍 fail-close。

Future global candidate:
`NOAA_GFS_V17_THOMPSON_FUTURE`

截至 2026-09-16 尚非 operational；不得提前切換。

## Current Gate
- `CURRENT_GLOBAL_DIRECT_DMAX_ELIGIBLE=false`
- `CURRENT_GLOBAL_SCHEME_PSD_RECONSTRUCTION_ELIGIBLE=false`
- `MAPPING_CANDIDATE_ELIGIBLE=false`
- `PRODUCTION_ICE_OPTICS_READY=false`
- `physics_promotion_allowed=false`

## New CASE Evidence
- `ice_microphysics_global_mapping_candidate_registry.csv`
- `ice_microphysics_global_mapping_qualification_gate.csv`
- `ice_microphysics_global_mapping_candidate_contract.json`

## Frozen Science
Formation / Viewing / Twilight Glow、六波段、Canvas/Corridor/REZ、Earth Shadow、Production/Shadow COT、Missing ≠ Clear ≠ Zero 與 WINDY portable decoupling 全部不變。

## Next concrete task
**Step 3B — GFS v16 Exact Scheme Pinning**。
不得先寫 GFDL MPv3→GFSv16、effective-size→Dmax 或 mass-only→PSD 的 mapping。
