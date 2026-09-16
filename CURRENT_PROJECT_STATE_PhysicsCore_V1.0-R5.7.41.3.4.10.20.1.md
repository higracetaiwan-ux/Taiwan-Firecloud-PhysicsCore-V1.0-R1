# CURRENT PROJECT STATE — Taiwan Firecloud PhysicsCore V1.0

## Current Version

`V1.0-R5.7.41.3.4.10.20.1`

Status: **QA PASS — FIELD VALIDATION PENDING**

Science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`

Latest formal FIELD baseline: `V1.0-R5.7.41.3.4.10.19 FIELD PASS`

## Current Milestone

Ice Optics Phase 2 Step 3G — **Primary Wyser Eq.(5)/(6) Numeric Recovery + Diagnostic Mass-Closure Preflight**

## Current Gate

`WYSER_PRIMARY_EQ5_EQ6_NUMERIC_RECOVERED_DIAGNOSTIC_MASS_CLOSURE_PASS_EXTERNAL_EQ6_CORROBORATION_BLOCKED`

- Primary Eq.(5) numeric recovered: YES
- Primary Eq.(6) numeric recovered: YES
- Eq.(5) independent transcription: PASS
- Eq.(6) external independent numeric corroboration: **PENDING / FAIL-CLOSED**
- Eq.(5)/(6) unit consistency: PASS
- Primary Eq.(6)+mixed PSD diagnostic mass closure: PASS
- Diagnostic integration convergence: PASS
- Scientific Wyser mass closure: NOT EXECUTED
- Absolute PSD reconstruction: BLOCKED
- L→Yang/Bi Dmax: BLOCKED
- Production Ice Optics: BLOCKED

## Recovered Numeric Contract

### Eq.(5)

```text
L/D = 1                              L < 30 µm
L/D = 1 + 0.003(L - 30 µm)          L >= 30 µm
D = L / (L/D)
```

### Eq.(6)

```text
m_g(L_um) = 2.311e-2 * (L_um / 1e4)^2.7625
```

`D=2.5 L^0.6` is retained only as a separate Wyser & Yang (1998) geometry lineage and is not Wyser (1998) Eq.(5).

## Diagnostic Mass-Closure Evidence

- T grid: `233.16 / 253.16 / 273.16 K`
- IWC grid: `0.001 / 0.1 / 10 g m^-3`
- Numerical resolutions: `1025 / 4097`, reference `32769`
- Cases: `18`
- Max mass-closure relative error: approximately `3.55e-16`
- Max branch continuity relative error: approximately `1.25e-15`
- Max normalization convergence relative error: approximately `8.20e-7`

These are numerical-preflight points only and are not an asserted operational validity domain.

## WINDY Handoff Readiness

Portable consumer/interface work may continue, but production Ice Optics remains blocked. `twfc.validated-ice-dmax-mapping.v1_1` must continue fail-close because L→Dmax, habit, roughness and independent optical validation are not complete.

## Next Step

Obtain independent external Eq.(6) numeric corroboration. After that gate passes, execute promotable scientific mass-closure validation over an explicitly justified physical T/IWC domain, then validate the Wyser L→Yang/Bi maximum-dimension geometry bridge.
