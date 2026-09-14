# Release Notes — V1.0-R5.7.41.3.4.10.9.9

## Added
- CAMS `PRESSURE_LEVEL_CHEMISTRY_OPTICS_BUNDLE` exact-union ADS request.
- Exact-source logical handoff to `O3_PRESSURE_LEVEL` and `NATIVE_AEROSOL_532NM_PRESSURE_LEVEL` when full 18-level coverage exists.
- Integrity `CAMS_PRESSURE_LEVEL_BUNDLE_EXACT_REUSE_PROVENANCE`.
- `FIRECLOUD_STATE_DIR_EXPLICIT_USER_OVERRIDE` worker contract.
- Dynamic DWD `shared_cache_scope` / `raw_cache_scope` provenance.

## Fixed
- `.10.9.8` app default `.firecloud_state` was indistinguishable from a true operator state-root override, so DWD cache remained release-local while audit claimed user-level cross-release.
- Isolated-job mode now isolates DWD raw cache as well as decoded optics.

## Runtime intent
TWS089 `.10.9.8` had four real CAMS ADS jobs after spectral-AOD exact reuse. `.10.9.9` best case reduces this to three real jobs by merging the two same-grid pressure-level jobs. Actual speedup is provider-dependent and requires Field validation.

## Science
No Frozen PhysicsCore science changes.
