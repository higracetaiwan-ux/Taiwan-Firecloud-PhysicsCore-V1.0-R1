# CURRENT PROJECT STATE — Taiwan Firecloud PhysicsCore V1.0

## Current Version

`V1.0-R5.7.41.3.4.10.21`

Status: **QA PASS — FIELD VALIDATION PENDING**

Science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`

Latest formal FIELD baseline: `V1.0-R5.7.41.3.4.10.20.1 FIELD PASS`

## Current Milestone

Ice Optics Phase 2 Step 3H — **Wyser → Yang/Bi Maximum-Dimension Coordinate Qualification + Shape Compatibility Gate**

## Current Gate

`WYSER_YANG_DMAX_COORDINATE_VALIDATED_SHAPE_COMPATIBILITY_BLOCKED`

### Passed

- Wyser `L` is the particle maximum-dimension coordinate: PASS
- Yang/Bi authoritative size axis is `maximum_dimension_um`: PASS
- `Wyser L_um == Yang/Bi maximum_dimension_um` as a **coordinate identity**: PASS
- Yang/Bi V2 `single_column` exact geometry source-row reproduction: PASS
- 189 source-derived `De=1.5V/A` rows reproduce the `3.48*sqrt(L)` large-column law with max relative error ≈ `5.84e-7`
- alternative `0.348*sqrt(L)` transcription is rejected by source geometry (max relative error ≈ `0.8973`)

### Still blocked

- Wyser ↔ Yang/Bi solid-column shape equivalence: BLOCKED
- projected-area equivalence: BLOCKED
- volume/mass equivalence: BLOCKED
- independent exact numeric corroboration for Wyser Eq.(6): BLOCKED
- scientific mass closure promotion: BLOCKED
- Yang/Bi habit bridge: BLOCKED
- roughness policy: BLOCKED
- bulk six-band Yang/Bi PSD integration: BLOCKED
- GFSv16 Dmax mapping: BLOCKED
- Production Ice Optics: BLOCKED
- `physics_promotion_allowed=false`

## Important semantic split

```text
Coordinate identity:
Wyser L_um == Yang/Bi maximum_dimension_um        PASS

Shape / optics identity:
Wyser solid column == Yang/Bi single_column       NOT PASS
```

The first statement only establishes a common maximum-dimension coordinate. It cannot be used to enable Dmax synthesis, habit selection, roughness selection, Ice τ, or Formation promotion.

## Yang/Bi V2 geometry reproduction

Pinned source geometry for the currently bundled authoritative V2 single-column family:

```text
a = 0.35 L                 L < 100 µm
a = 3.48 sqrt(L)           L >= 100 µm
width = 2a
```

The coefficient is qualified from the actual source-derived geometry in the bundled LUT rather than from an ambiguous literature transcription. The source rows preserve Yang/Bi `V` and projected-area semantics through `effective_diameter_um=1.5V/A`.

## WINDY Handoff Readiness

`twfc.validated-ice-dmax-mapping.v1_1` must remain fail-close. Step 3H validates a size-coordinate identity only; it does not provide a forecast-model Dmax mapping or a production habit/roughness decision.

## Next Step

Step 3I should validate the **Wyser ↔ Yang/Bi solid-column population geometry bridge** using source `V/A` and Wyser Eq.(5)/(6), while keeping Eq.(6) independent corroboration as a separate blocker. Only after shape/projected-area/volume-mass, habit, roughness and independent bulk-optics validation are passed may the six-band production integrator be promoted.
