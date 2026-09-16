# Test Report — PhysicsCore V1.0-R5.7.41.3.4.10.20

## TDD
- RED: Step 3G test initially failed because `ice_microphysics_wyser_primary_numeric_recovery` did not exist.
- GREEN: Step 3G primary tests **7/7 PASS** after implementation and integrity/archive wiring.

## Targeted regression
- Ice Optics / Step 3B–3G / Phase 2 / portable targeted suite: **88/88 PASS**.

## Working-tree full regression
- Group 1: **304 PASS**, 1 existing pandas FutureWarning
- Group 2: **311 PASS**
- Group 3: **220 PASS**
- Total: **835/835 PASS, 0 failed**

## Serialization probe
- Step 3G evidence: **12 rows / 6113 bytes**
- Step 3G gate: **1 row / 1466 bytes**
- Step 3G contract: **2930 bytes**
- Archive Content gates: **3/3 PASS**
- Synthetic closure relative error: approximately `1.73e-16`
- `scientific_mass_closure_pass=false` by design and contract.

## First packaged fresh-extract verification
- Extracted version: `1.0.0-R5.7.41.3.4.10.20`
- Group 1: **304 PASS**, 1 existing pandas FutureWarning
- Group 2: **311 PASS**
- Group 3: **220 PASS**
- Total: **835/835 PASS, 0 failed**

## Release state
`IMPLEMENTATION / REGRESSION PASS — FIELD VALIDATION PENDING`

The release is re-packaged after this report update and the final ZIP is independently fresh-extract verified before delivery.
