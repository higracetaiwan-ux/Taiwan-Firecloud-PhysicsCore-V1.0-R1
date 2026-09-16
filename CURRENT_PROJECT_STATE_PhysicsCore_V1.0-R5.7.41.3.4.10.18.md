# CURRENT PROJECT STATE — Taiwan Firecloud PhysicsCore V1.0

## Current Version
`V1.0-R5.7.41.3.4.10.18`

Status: **IMPLEMENTATION / REGRESSION PASS — FIELD VALIDATION PENDING**

Science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`
Latest formal FIELD baseline: `V1.0-R5.7.41.3.4.10.17 FIELD PASS`

## Current Milestone
Step 3E — **Wyser PSD Normalization + Hex-Column Geometry / L→Dmax Coordinate Qualification**

## Current gate
`WYSER_NORMALIZATION_RULE_PINNED_EXECUTION_GEOMETRY_BLOCKED`

Pinned:
- IWC-constrained PSD amplitude rule `A=IWC/∫m phi dL`。
- mixed PSD shape / 20 µm continuity / ν=3 / λ=0.3。
- GFS-v16 B(T,IWC) equivalent。

Blocked:
- exact numeric mass-size contract。
- absolute PSD numeric execution。
- exact Wyser column geometry。
- L→Yang/Bi Dmax coordinate。
- mass closure validation。
- habit / roughness / independent validation。

Production state:
- `BULK_YANG_BI_PSD_INTEGRATION_ELIGIBLE=false`
- `GFSV16_DMAX_MAPPING_ELIGIBLE=false`
- `PRODUCTION_ICE_OPTICS_READY=false`
- `physics_promotion_allowed=false`

## Next
FIELD validate `.10.18`. 通過後進 Step 3F，優先取得 exact Wyser Eq.(5)/(6) geometry+mass-size contract，再建立 diagnostic mass-closure reconstruction；不可用二手 geometry 靜默補值。
