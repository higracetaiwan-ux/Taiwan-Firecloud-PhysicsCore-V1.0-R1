# R5.7.33 — Twilight Glow Deep-Range Gas/Rayleigh/Cloud Closure

## Scope

R5.7.33 addresses the final ten `Scatter→Observer` Partial rows exposed by the
R5.7.32 field CASE. It does not add aerosol SSA, aerosol phase functions,
multiple scattering, or absolute radiance calibration.

## Field root cause split

The immutable R5.7.32 2026-09-09 sunset CASE contained 10/1092 Partial observer
extinction rows, all at 100 km and solar altitude −5.5°/−6°:

1. Six z=3.75 km rows were molecular boundary touches. The first LOS midpoint
   was about 74.62 m AGL while the lowest real pressure-profile level was about
   75.07 m AGL, a difference of only ~0.45 m.
2. Four z=7.75 km rows were genuine cloud optical evidence conflicts. The LOS
   crossed a layer with cloud fraction 0.1 but explicit zero native condensate,
   no COT, `target_optical_truth_state=DIRECT_EVIDENCE_CONFLICT`, and
   `target_cot_semantics=UNRESOLVED_CONFLICT`.

## Molecular boundary policy

Glow Rayleigh and HITRAN gas-species observer paths now reuse the already-frozen
Gas RT lowest-native pressure-profile boundary tolerance:

- tolerance: `<= 0.01 km`;
- only the lowest real native pressure-profile endpoint may be used;
- no upper-profile extrapolation;
- no synthetic temperature, pressure, O3, O2, or H2O state;
- values beyond tolerance remain Partial/Missing.

This is a boundary-touch policy, not profile extrapolation.

## Cloud conflict policy

R5.7.33 does **not** turn cloud optical conflicts into clear sky.

When an observer ray intersects a blocker whose COT is unresolved because native
evidence conflicts (for example `CF_CLOUD_CONDENSATE_ZERO`), Glow exports:

`GLOW_OBSERVER_CLOUD_DIRECT_EVIDENCE_CONFLICT_PRESERVED`

and retains:

- cloud tau = Missing;
- band evidence = Missing;
- observer extinction = Partial;
- no COT inferred from cloud fraction;
- no tau=0 inferred from zero condensate.

Thus `Missing != Clear != Zero` remains frozen.

## New provenance

The Glow observer extinction export adds:

- `glow_observer_molecular_lowest_endpoint_tolerance_km`
- `glow_observer_molecular_boundary_policy`
- `glow_observer_cloud_evidence_state`
- cloud blocker/unresolved/conflict counts
- unresolved layer IDs and conflict-state provenance
- `twilight_glow_deep_range_closure_contract`

## New Integrity guards

- `TWILIGHT_GLOW_OBSERVER_DEEP_RANGE_MOLECULAR_COVERAGE`
  - when real gas profiles are ready, every 100 km Glow observer volume must
    have resolved Rayleigh + gas-species paths and finite six-band
    Rayleigh/non-O3/O3 tau.
- `TWILIGHT_GLOW_OBSERVER_CLOUD_CONFLICT_PRESERVATION`
  - unresolved cloud blockers must be explicitly classified;
  - conflict/missing cloud tau must never be promoted to zero or FULL evidence.

## Forensic replay acceptance

Using the immutable R5.7.32 field CASE without changing provider data:

- 100 km Rayleigh: 156/156 resolved;
- 100 km gas species: 156/156 resolved;
- previous six z=3.75 km molecular partials: 14/14 segments resolved;
- four z=7.75 km cloud conflicts: explicitly preserved as conflict/Missing.

Expected observer extinction after the intended correction is therefore
1088/1092 Full, not 1092/1092. The remaining four Partial rows are physically
honest evidence conflicts, not a runtime defect.

## Frozen/non-goals

Unchanged:

- Formation `Sun→CloudBase`;
- Viewing `Cloud→Observer` decision semantics;
- Photography Formation-first gate;
- independent Glow branch;
- 13 solar angles;
- six wavelengths 550/575/600/650/700/750 nm;
- Route Invariance and provider cycle freeze;
- R5.7.32 CAMS geopotential normalization and Glow aerosol endpoint policy;
- no aerosol SSA/phase function yet;
- no multiple scattering yet;
- no absolute sky radiance claim.
