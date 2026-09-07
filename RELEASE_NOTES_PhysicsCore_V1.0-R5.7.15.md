# PhysicsCore V1.0-R5.7.15 Release Notes

## Scope
Target Canvas Optical Evidence Closure. No UI consolidation and no change to scientific thresholds/weights.

## Changes
- Added `target_optical_truth_state`.
- Added `target_cot_semantics`.
- Added `target_response_eligibility`.
- Added `cf_or_rh_used_to_infer_cot=False` audit contract.
- Extended target optical summary with exact/bounded/conflict/unknown counts, fractions, and `closure_state`.
- Formation canvas/summary carries the same optical-truth provenance for downstream auditing.

## Frozen semantics
- Missing != Clear != Zero.
- Cloud fraction != COT.
- RH != COT.
- `CF_CLOUD_CONDENSATE_ZERO` is a direct evidence conflict, not zero optical depth.
- Secondary forecast-native optics may not erase a primary direct conflict.
- Target cloud optical response remains separate from Sun->CloudBase path RT.

## Formal replay on R5.7.14 CASE evidence
- CASE A: 107 Canvas targets/angle = 43 exact + 64 direct-conflict.
- CASE B: 70 Canvas targets/angle = 4 exact + 66 direct-conflict.
- No bounded or unknown targets in these two replay cases.
- Both therefore close as `CONFLICT_UNRESOLVED`, not `MISSING`.

## Tests
325 passed / 0 failed.
