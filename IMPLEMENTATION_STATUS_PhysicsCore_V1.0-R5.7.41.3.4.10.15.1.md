# IMPLEMENTATION STATUS — V1.0-R5.7.41.3.4.10.15.1

## Status
**IMPLEMENTATION / REGRESSION PASS — FIELD VALIDATION PENDING**

## FIELD trigger
`.10.15 / TWS100 / 2026-09-17 sunrise` exposed a CASE evidence handoff defect:
the Step 3B model evidence passed Analysis Integrity but was serialized into CASE as empty CSV/JSON placeholders.

## Implemented
1. CASE export rebuilds Step 3B release-static scheme-pin evidence from the running release.
2. Step 3B CASE payload is independent of UI/session result-key survival.
3. Archive Integrity now verifies actual serialized content:
   - evidence >= 8 rows
   - gate >= 1 row
   - contract JSON > 2 bytes
4. Exact `.10.15` failure shape has a dedicated regression test.
5. No science or provider changes.

## Verification
- targeted regression: 22/22 PASS
- full working-tree regression: 800/800 PASS
- first packaged fresh-extract regression: 800/800 PASS
- synthetic serialized Step 3B evidence:
  - evidence: 8 rows / 4212 bytes
  - gate: 1 row / 1095 bytes
  - contract: 1620 bytes
  - archive-content gates: 3/3 PASS

## Frozen
`R5.7.41.2_SHADOW_COT_AB_FROZEN`

No Dmax mapping, PSD reconstruction, habit default, roughness default, or production promotion is enabled.
