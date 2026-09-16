# IMPLEMENTATION STATUS — V1.0-R5.7.41.3.4.10.16

Status: **IMPLEMENTATION / REGRESSION PASS — FIELD VALIDATION PENDING**

## Completed
- Added `firecloud/ice_microphysics_gfsv16_rei_dmax_bridge.py`.
- Recorded the `reiflag=2` public-source formula path and the documentation/source label mismatch.
- Rejected direct `rei→Dmax`, `2×rei→Dmax`, generalized-effective-diameter→Dmax and effective-radius bounds→Dmax shortcuts.
- Identified a bulk PSD integration path using Yang/Bi single-particle optics without enabling it.
- Added Step 3C Analysis Integrity gates.
- Added Step 3C CASE Archive required-member and serialized-content gates.
- CASE export rebuilds Step 3C release-static evidence from the running release.
- Frozen Science unchanged.

## Not completed / intentionally blocked
- Exact operational NCEP binary commit provenance.
- Exact Wyser PSD/aspect-ratio reconstruction.
- Yang/Bi habit mapping.
- Yang/Bi roughness mapping/ensemble.
- Bulk integration implementation.
- Dmax mapping eligibility.
- Production Ice Optics promotion.

## Verification
Working-tree full regression: **807 passed, 0 failed, 1 existing warning**.
First packaged fresh-extract regression: **807 passed, 0 failed** (254 + 363 + 190), with the same existing pandas FutureWarning. Final ZIP will be rebuilt after report update and verified again.
