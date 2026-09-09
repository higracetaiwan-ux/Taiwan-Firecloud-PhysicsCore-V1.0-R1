# PhysicsCore V1.0-R5.7.31 Implementation Status

Status: **CODE COMPLETE — DEPLOYMENT FIELD VALIDATION REQUIRED**

Implemented:

- explicit six-band `Sun→Scatter` extinction components;
- explicit six-band `Scatter→Observer` extinction components;
- O3 / non-O3 HITRAN gas decomposition without double counting;
- explicit total optical depth and `exp(-tau)` closure only when all components are complete;
- three new CASE evidence CSVs for the two path legs and final single-scattering proxy;
- R5.7.31-specific Integrity target coverage, schema, Sun-path closure, observer-path closure,
  and source-proxy closure;
- historical R5.7.30 CASEs are not retroactively subjected to R5.7.31-only guards;
- Formation, Viewing, Photography, Red-Light Availability, 13 angles, six bands, route
  resolution and provider policy remain unchanged.

Verification:

- focused R5.7.30/R5.7.30.1/R5.7.31 regression: 12 passed / 0 failed;
- full working-tree regression: 486 passed / 0 failed.

Field acceptance remains OPEN until a new R5.7.31 CASE confirms Analysis Integrity and CASE
Integrity PASS and the new Glow extinction tables cover the complete runtime volume domain.
