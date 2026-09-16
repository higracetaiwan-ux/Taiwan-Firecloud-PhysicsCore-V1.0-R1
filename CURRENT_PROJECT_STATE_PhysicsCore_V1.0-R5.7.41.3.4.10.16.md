# CURRENT PROJECT STATE — Taiwan Firecloud PhysicsCore V1.0

## Current Version
`V1.0-R5.7.41.3.4.10.16`

Status: **IMPLEMENTATION / REGRESSION PASS — FIELD VALIDATION PENDING**

Latest FIELD PASS: **`V1.0-R5.7.41.3.4.10.15.1 FIELD PASS`**

Science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`

## Current Milestone
Ice Optics Phase 2 Step 3C — **GFS v16 Effective-Radius ↔ Yang/Bi Dmax Bridge Feasibility Audit**

## Core Decision
Direct one-to-one conversion from GFDL/Wyser bulk cloud-ice effective radius `rei` to Yang/Bi `maximum_dimension_um` is rejected.

Current state:
- GFS v16-compatible public GFDL v1/2019 source path: pinned.
- `reiflag=2` actual v1 source formula: pinned as Wyser-labeled bulk `rei` branch.
- public parameter-comment vs source-branch label: **mismatch recorded**.
- Yang/Bi primary optical size axis: `maximum_dimension_um`.
- direct `rei→Dmax`: **NOT ELIGIBLE**.
- bulk PSD integration path: **IDENTIFIED, NOT QUALIFIED**.
- Dmax mapping: disabled.
- production Ice Optics: disabled.

Qualification state:
`DIRECT_DMAX_BRIDGE_REJECTED_BULK_PSD_PATH_IDENTIFIED_NOT_QUALIFIED`

## New Step 3C CASE Evidence
- `ice_microphysics_gfsv16_rei_dmax_bridge_evidence.csv`
- `ice_microphysics_gfsv16_rei_dmax_bridge_gate.csv`
- `ice_microphysics_gfsv16_rei_dmax_bridge_contract.json`

These are release-static evidence rebuilt at CASE export time, with Analysis Integrity, archive required-member, and archive-content gates.

## Regression
- Step 3C TDD test: initial RED confirmed module absent.
- Step 3C primary tests: 7/7 PASS.
- targeted Ice/Phase2/Step2/Step3/Step3B tests: 60/60 PASS.
- full working-tree regression: **807/807 PASS**.
- existing pandas FutureWarning: 1.
- FIELD validation: pending.

## Current WINDY Handoff Readiness
The portable interface and WINDY integration contract may continue development, but final production Ice Optics handoff remains blocked by:
1. exact Wyser PSD/aspect-ratio reconstruction;
2. Yang/Bi habit compatibility qualification;
3. roughness state/uncertainty qualification;
4. bulk optical integration uncertainty/domain;
5. independent validation;
6. production promotion gate;
7. final certified WINDY portable bundle / validated mapping response.

## Next Step after `.10.16 FIELD PASS`
**Step 3D — Wyser PSD + Yang/Bi Habit Bulk-Integration Contract Qualification**

Do not create a scalar `r_eff→Dmax` rule. Instead pin the population distribution and geometry needed to integrate the authoritative Yang/Bi Dmax LUT into bulk six-band ice optics.
