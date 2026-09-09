# Taiwan Firecloud PhysicsCore — Current Project State

狀態版本：**V1.0-R5.7.32**
狀態日期：2026-09-09（Asia/Taipei）

## Current production candidate

`Taiwan-Firecloud-PhysicsCore-V1.0-R5.7.32-FULL-CLEAN.zip`

## R5.7.32 focus

- Correct CAMS geopotential (`m**2 s**-2`) → geopotential height metres.
- Fail-close unknown provider units.
- Glow-only <=0.05 km lowest-native aerosol endpoint tolerance.
- Integrity guard for CAMS height normalization.
- Integrity guard for 60/80/100 km Glow observer aerosol six-band coverage.

## Frozen

13 angles; six bands 550/575/600/650/700/750 nm; Formation/Viewing/Glow separation; Photography Formation-first gate; Route Invariance; Missing != Clear != Zero; Forecast/Observation/Nowcast separation.

## Validation

- working-tree regression: 492 PASS / 0 FAIL
- R5.7.31 immutable CASE forensic replay: 468/468 long-range aerosol resolved after intended R5.7.32 corrections
- new R5.7.32 field CASE: OPEN
