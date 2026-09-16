# CURRENT PROJECT STATE — Taiwan Firecloud PhysicsCore V1.0

## Current Version
`V1.0-R5.7.41.3.4.10.17`

Status: **IMPLEMENTATION / REGRESSION PASS — FIELD VALIDATION PENDING**

Science baseline:
`R5.7.41.2_SHADOW_COT_AB_FROZEN`

Latest formal FIELD baseline:
`V1.0-R5.7.41.3.4.10.16 FIELD PASS`

## Current Milestone
Ice Optics Phase 2 Step 3D —
**Wyser PSD + Yang/Bi Habit Bulk-Integration Contract Qualification**

## Step 3D Gate
`WYSER_PSD_CORE_PINNED_GEOMETRY_HABIT_ROUGHNESS_BLOCKED`

Pinned:
- mixed Gamma + power-law PSD structure
- 20 μm switch / continuity constraint
- ν=3, λ=0.3 μm^-1
- nominal integration limits L=10–1000 μm
- GFS-v16 public-source B(T,IWC) equivalent
- Yang/Bi Dmax domain
- Yang/Bi three roughness states
- six-band bulk integration mathematics

Still unresolved:
- absolute PSD normalization
- exact primary-source column aspect-ratio law
- Wyser L → Yang/Bi Dmax coordinate bridge
- exact habit compatibility
- roughness production policy
- independent bulk-optics validation

Current capability:
- `BULK_YANG_BI_PSD_INTEGRATION_ELIGIBLE=false`
- `GFSV16_DMAX_MAPPING_ELIGIBLE=false`
- `PRODUCTION_ICE_OPTICS_READY=false`
- `physics_promotion_allowed=false`

## WINDY Handoff
Portable interface work can continue.
Final production Ice Optics package still waits on:
1. exact PSD normalization;
2. geometry / L→Dmax bridge;
3. habit qualification;
4. roughness uncertainty policy;
5. independent six-band validation;
6. production promotion gate;
7. certified WINDY portable bundle.
