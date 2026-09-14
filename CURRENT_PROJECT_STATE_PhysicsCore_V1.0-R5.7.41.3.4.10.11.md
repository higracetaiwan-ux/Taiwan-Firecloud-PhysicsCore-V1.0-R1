# Taiwan Firecloud PhysicsCore — Current Project State

> Version: **V1.0-R5.7.41.3.4.10.11**  
> Internal: `1.0.0-R5.7.41.3.4.10.11`  
> Science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`

## Current release status

- `.10.10.1 = FIELD PASS`
- `.10.10.2 = FIELD PASS`
- `.10.11 = REGRESSION PASS / AUTHORITATIVE SOURCE BUILD READY / FIELD RETEST CANDIDATE`

## Current mainline

Development has left UI/runtime optimization as the main line and returned to scientific capability.

The active science workstream is **Ice Cloud Spectral Optics**.

### Architecture

PhysicsCore remains the authoritative authoring / calibration / QA / release environment for Ice Optics.

WINDY Firecloud Observer consumes a versioned standalone portable package and does not require PhysicsCore/Python/Streamlit at runtime.

### Authoritative source

Selected source: Yang/Bi V2 ice-particle single-scattering database, Zenodo record 5348402.

R5.7.41.3.4.10.11 now provides the strict source-to-LUT build gate. It does not bundle the 27.4 GB source archive and therefore does not yet claim a calibrated production LUT.

### Frozen rules preserved

- Formation = Sun → CloudBase
- Viewing = Cloud → Observer
- Twilight Glow = independent third branch
- 550/575/600/650/700/750 nm
- Canvas 0–40 / 40–100 km
- Dynamic Corridor / REZ
- Earth Shadow / Penumbra
- Production vs Shadow COT separation
- Missing != Clear != Zero
- Ice Optics remains diagnostic/no-promotion until a later explicit Phase-3 release gate

## Next concrete task

Obtain/verify the published `Data_0.2_15.25.tar.gz` archive, extract its 27 `isca.dat` source tables, run the `.10.11` authoritative build gate, inspect spectral interpolation and size-coordinate QA, then emit the first calibrated `Firecloud-Ice-Optics-Portable` package for WINDY independent runtime testing.
