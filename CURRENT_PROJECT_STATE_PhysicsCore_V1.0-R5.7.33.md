# Taiwan Firecloud PhysicsCore — Current Project State

狀態版本：**V1.0-R5.7.33**
狀態日期：2026-09-09（Asia/Taipei）

## Current production candidate

`Taiwan-Firecloud-PhysicsCore-V1.0-R5.7.33-FULL-CLEAN.zip`

## Previous field closure

R5.7.32 field CASE is CLOSED:

- Analysis Integrity: 50/50 PASS
- CASE Integrity: 22/22 PASS
- CAMS geopotential normalization: PASS
- 60/80/100 km Glow observer aerosol: 468/468 resolved
- observer extinction: 1082/1092 Full; remaining 10 Partial isolated to molecular boundary touches and cloud evidence conflicts

## R5.7.33 focus

- reuse frozen <=0.01 km lowest-native gas profile boundary tolerance for Glow Rayleigh/gas-species observer integration;
- require 100 km molecular six-band coverage when gas profile evidence is ready;
- explicitly classify/preserve cloud optical evidence conflicts;
- never infer COT from cloud fraction or zero condensate;
- no SSA / aerosol phase function / multiple scattering yet.

## Frozen

13 angles; six bands 550/575/600/650/700/750 nm; Formation/Viewing/Glow separation; Photography Formation-first gate; Route Invariance; Missing != Clear != Zero; Forecast/Observation/Nowcast separation.

## Validation

- R5.7.32 immutable CASE forensic replay under intended R5.7.33 logic:
  - 100 km Rayleigh 156/156 resolved
  - 100 km gas species 156/156 resolved
  - four cloud conflicts preserved as Missing/Partial
  - expected observer Full 1088/1092, not 1092/1092
- R5.7.33 new field CASE: OPEN
- final regression/package validation: pending
