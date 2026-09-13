# Taiwan Firecloud PhysicsCore — Current Project State

Current release: **V1.0-R5.7.41.3.4.10.7 — Viewing↔Glow Shared Hydrometeor Context**

Science baseline remains frozen at `R5.7.41.2_SHADOW_COT_AB_FROZEN`.

## Runtime roadmap status

- `.10.1` Observer Aerosol Numeric Route Context：FIELD PASS
- `.10.2` Molecular Numeric Route Context：FIELD PASS
- `.10.3` Observer Precipitation Horizontal-Support Ray Reuse：FIELD PASS
- `.10.4` Gas Spectroscopy State Memo：FIELD PASS
- `.10.5` Route Group Direct Reuse：science exactness PASS / runtime NOT FIELD PASS
- `.10.6` Cloud Numeric Route Context：FIELD PASS（2026-09-14 sunrise TWS091 observer spectral 2.740815 s）
- `.10.7` Viewing↔Glow Shared Hydrometeor Context：REGRESSION PASS / FIELD TEST CANDIDATE

## `.10.7` purpose

Main Viewing and Glow previously rebuilt identical native hydrometeor route contexts independently. `.10.7` prepares once per exact `(time, solar_altitude_deg)` and reuses the immutable cells/support groups across the two branches. Target-specific LOS integration remains independent.

## Baseline for next Field run

2026-09-14 sunrise TWS091 `.10.6`:
- Glow Observer Precipitation 8.250749 s
- Glow Volume Assembly 8.073043 s
- Glow Lookup Context Prep 7.456110 s
- Glow Observer Spectral 2.740815 s
- Glow total 29.901809 s

Primary `.10.7` Field gate: Glow Observer Precipitation must materially decline without science drift under provider-consistent evidence.
