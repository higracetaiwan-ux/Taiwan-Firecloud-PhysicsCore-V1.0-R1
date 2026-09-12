# Taiwan Firecloud PhysicsCore — Current Project State

Current candidate: **V1.0-R5.7.41.3.4.2**.

## Trigger
2026-08-30 Sunrise TWS175 historical replay under R5.7.41.3.4.1 proved AWS indexed-range fallback is operational, but primary pgrb2 returned ICMR and other fields while CLWMR remained absent from the selected subset.

## Change
Add transport/decode naming compatibility for NCEP Cloud Mixing Ratio aliases `CLMR` and `CLWMR`. No inferred values. Missing remains Missing.

## Frozen science
`R5.7.41.2_SHADOW_COT_AB_FROZEN`; no Production switch; no COT/Formation promotion.

## Next Field validation
Repeat exactly 2026-08-30 Sunrise TWS175. PASS criterion: AWS fallback remains same run/lead, and if the archive uses CLMR the primary native completeness should recover CLWMR canonical rows. If neither alias exists, retain Missing and inspect producer-side field availability.

## Release status
Working-tree 609/609 PASS; trial fresh-extract 609/609 PASS; final fresh-extract 609/609 PASS. Release Gate CLOSED.
