# Taiwan Firecloud PhysicsCore V1.0-R4.9

## Target Canvas Optical Evidence Resolver

R4.9 formalizes target-cloud optical evidence as a separate contract before Formation.

### Added
- `v1_target_canvas_optical_evidence.csv`
- `v1_target_canvas_optical_summary.csv`
- exact direct-native target COT state: `DIRECT_NATIVE_CONDENSATE_COT`
- bounded two-sided adjacent-native state: `ADJACENT_NATIVE_COT_BRACKET_BOUNDED`
- explicit conflict state: `CF_CLOUD_CONDENSATE_ZERO_UNRESOLVED`

### Physics rules
- Cloud Fraction, RH and cloud geometry never synthesize COT.
- Explicit native condensate zero cannot be overwritten by spatial interpolation.
- Bounded adjacent interpolation is allowed only for missing target optics, only from immediately adjacent sampled nodes on the same direction, and only with vertically overlapping native-condensate COT on both sides.
- Sampling spacing is numerical interpolation support, never physical cloud width.
- Bounded target COT is exported as uncertainty and is not promoted to exact Tier-1 Formation radiance.

### Expected R4.8.1 golden-case result
The 2026-09-05 sunset case is expected to remain unresolved for target optics where all Canvas layers are `CF_CLOUD_CONDENSATE_ZERO`; R4.9 should diagnose that explicitly rather than fabricate target COT.

### Validation
- R4.9 focused target-optics / formation / geometry-optics tests: 12 passed.
- Full suite: 232 passed, 10 known stale/legacy-contract failures. No new R4.9 target-optics regression failure.
