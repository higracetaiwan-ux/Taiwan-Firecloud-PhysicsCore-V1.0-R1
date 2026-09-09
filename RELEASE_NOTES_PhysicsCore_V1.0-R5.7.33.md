# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.33

## Theme

**Twilight Glow Deep-Range Gas/Rayleigh Boundary Closure + Cloud Conflict Preservation**

## Fixed

1. Glow `Scatter→Observer` Rayleigh integration now reuses the frozen 10 m
   lowest-native gas pressure-profile boundary tolerance.
2. Glow O3/O2/H2O gas-species integration uses the same lowest-native endpoint
   rule; no upper-profile or beyond-tolerance extrapolation is introduced.
3. Genuine cloud optical conflicts are explicitly exported as
   `GLOW_OBSERVER_CLOUD_DIRECT_EVIDENCE_CONFLICT_PRESERVED` rather than being
   conflated with clear sky or zero optical depth.
4. Added deep-range molecular coverage and cloud-conflict preservation
   Integrity guards.
5. Added molecular boundary and cloud conflict provenance to the existing Glow
   observer extinction CASE export.

## Immutable R5.7.32 forensic replay

The six previous 100 km z=3.75 km molecular partial rows become 14/14 segment
resolved for both Rayleigh and gas species. All 156/156 100 km molecular targets
resolve. The four z=7.75 km cloud partial rows remain Partial by design because
they are native optical evidence conflicts.

This implies an expected observer-path state of **1088/1092 Full + 4/1092
conflict-preserved Partial** for that old CASE. Old CASE files are not rewritten.

## Regression

Final regression: PENDING_FINAL_PACKAGE_VALIDATION.

## Field status

OPEN — requires a new R5.7.33 CASE. Regression and forensic replay are not field
validation.
