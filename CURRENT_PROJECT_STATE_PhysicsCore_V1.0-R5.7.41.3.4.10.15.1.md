# CURRENT PROJECT STATE — Taiwan Firecloud PhysicsCore V1.0

## Current Version
`V1.0-R5.7.41.3.4.10.15.1`

Status: **IMPLEMENTATION / REGRESSION PASS — FIELD VALIDATION PENDING**

Last formal FIELD PASS:
`V1.0-R5.7.41.3.4.10.14`

Science baseline:
`R5.7.41.2_SHADOW_COT_AB_FROZEN`

## Current Milestone
Ice Optics Phase 2 Step 3B —
**GFS v16 Scheme Pinning + CASE Evidence Handoff Integrity Hotfix**

## `.10.15` FIELD Finding
CASE:
`2026-09-17 sunrise / TWS100 合歡山北峰`

Physics/Ice fail-close was correct, but Step 3B CASE evidence serialization failed:
- scheme-pin evidence CSV: 0 rows
- scheme-pin gate CSV: 0 rows
- scheme-pin contract JSON: `{}`

The old presence-only CASE archive gate still reported PASS. Therefore `.10.15` is FIELD FAIL for evidence-chain integrity and is not a valid FIELD baseline.

## `.10.15.1` Fix
- Step 3B CASE artifacts are rebuilt directly from exact running-release builders at CASE export.
- Archive Integrity checks serialized content, not filename presence only.
- Empty Step 3B placeholders cause hard FAIL.
- No science/model/provider changes.

## Current GFS v16 Scheme State
Pinned:
- microphysics family: GFDL Cloud Microphysics
- public reproduction path: `physics/MP/GFDL/v1_2019`
- GFS_v16 emulation `reiflag=2`
- semantic: cloud-ice effective radius, not maximum dimension

Unresolved:
- NCEP production binary exact commit
- effective-radius → Yang/Bi Dmax semantic bridge
- habit
- surface roughness
- independent Dmax mapping validation

Therefore:
- `GFSV16_DMAX_MAPPING_ELIGIBLE=false`
- `GFSV16_PSD_RECONSTRUCTION_ELIGIBLE=false`
- `PRODUCTION_ICE_OPTICS_READY=false`
- `physics_promotion_allowed=false`

## Regression
- targeted handoff/integrity regression: 22/22 PASS
- full working-tree regression: 800/800 PASS
- fresh-extract regression: 800/800 PASS
- 0 failures
- 1 existing pandas FutureWarning

## Next
Run a `.10.15.1` FIELD CASE and require:
1. `ice_microphysics_gfsv16_scheme_pin_evidence.csv` >= 8 rows;
2. `ice_microphysics_gfsv16_scheme_pin_gate.csv` >= 1 row;
3. `ice_microphysics_gfsv16_scheme_pin_contract.json` non-empty;
4. three Step 3B Analysis Integrity gates PASS;
5. three Step 3B archive member gates PASS;
6. three new Step 3B archive-content gates PASS;
7. positive-IWP Ice rows remain Dmax/PSD/tau/promotion fail-close.
