# Taiwan Firecloud PhysicsCore V1.0-R3.3 Release Notes

R3.3 is a performance-foundation release for the Stage-2 optical path. It does not change the frozen Formation/Viewing/Decision physics.

## Implemented

- Added default **Canvas-candidate RT target filtering**. The native 3-D cloud volume remains intact for geometry/blocker intersections, while expensive spectral target RT is reduced to one nearest native optical target per active Canvas base.
- Added `FIRECLOUD_V1_RT_TARGET_MODE=ALL_VOXELS` compatibility switch for legacy full-voxel spectral diagnostics.
- Added reusable `GasRTPreparedContext` per forecast/CAMS state so Runtime LUT preparation and route gas-profile indexing are not rebuilt for every solar angle.
- Reuses the already cached route spectral-AOD derivation inside `build_spectral_rt()` instead of deriving the same spectral AOD again per angle.
- Added performance diagnostics: `V1_RT_CANDIDATE_FILTER` and `GAS_RT_PREPARED_CONTEXT`.
- Preserves the R3.1 fail-closed rules: geometry-only cloud optics remain Unknown, precipitation optical depth is never invented, and Missing never becomes clear/zero.

## 550 nm spectroscopy status

The program supports the frozen six-band contract `550/575/600/650/700/750 nm`, but the packaged compatibility Runtime LUT still lacks a verified complete 550-nm H2O/O2/O3 T/P spectroscopy grid. 550-nm gas RT therefore remains Missing until a real six-band LUT is built/imported from local spectroscopy inputs. No neighbouring-band interpolation is used.

## Validation boundary

R3.3 includes unit/regression coverage for Canvas target filtering, legacy all-voxel fallback, gas-preparation fail-closed behavior, R3.2 six-band activation, R3.1 Missing semantics, and R3 OpticalPath contracts. Wall-clock improvement must still be confirmed with the same live CASE because CAMS network/cache time varies between runs.
