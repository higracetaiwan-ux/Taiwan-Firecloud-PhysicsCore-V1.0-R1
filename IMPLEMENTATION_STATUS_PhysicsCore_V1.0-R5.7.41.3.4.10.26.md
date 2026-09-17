# Implementation Status — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.26

## Step 3M — Yang/Bi Matched-Geometry Extinction Validation

### Implemented
- `firecloud/ice_microphysics_yang_matched_geometry_extinction_validation.py`
- same-Yang-geometry Fu96 `Cext≈2A` extinction reference chain
- 1,962 single-particle comparison rows
- 18-case / 324-row matched-geometry bulk validation matrix
- Step 3M 12-row evidence / 1-row gate / JSON contract
- model result wiring / performance telemetry
- CASE archive handoff / archive-integrity required members
- analysis integrity fail-close checks
- UI current milestone / release history
- Step 3M core / handoff / stable-contract / release-identity regressions

### Preserved
- Frozen science baseline `R5.7.41.2_SHADOW_COT_AB_FROZEN`
- Step 3L runtime habit/roughness fail-close
- full-double scientific calculation path
- independent SSA/g blockers
- `tau_ice` / production ice optics / physics promotion blockers
- Formation / Viewing / Twilight Glow separation

### QA
- Working-tree regression：903/903 PASS。
- Candidate FULL-CLEAN fresh-extract：903/903 PASS。
- Candidate Step 3M evidence / gate / contract：byte-exact PASS。
- FIELD：pending；formal FIELD baseline remains `.10.25.1 FIELD PASS`.
