# Taiwan Firecloud PhysicsCore V1.0-R5.1 Release Notes

## ECMWF IFS Secondary Native Cloud Microphysics Provider

R5.1 replaces the R5.0 empty provider hook with a working, fail-closed IFS GRIB decoder/physics bridge for entitled or mounted ECMWF forecast GRIB files.

- Reads IFS hybrid model-level CLWC, CIWC, CC, T, Q; optional CRWC/CSWC.
- Reads hybrid A/B coefficients and surface pressure/geopotential and reconstructs model-level AGL height hydrostatically.
- Derives visible cloud extinction/COT from native condensate using explicit liquid/ice effective-radius assumptions; provenance is retained.
- Never converts cloud fraction, RH, cloud geometry, satellite imagery, or surface rain rate into COT.
- Source discovery uses `FIRECLOUD_ECMWF_IFS_GRIB_PATH` or `FIRECLOUD_ECMWF_IFS_GRIB_DIR`. If no entitled forecast GRIB is present, the provider returns explicit Missing rather than fabricating evidence.
- Adds `ecmwf_ifs_request_audit.csv` and populates `v1_secondary_target_optics.csv` when valid native IFS cloud optics are available.

## Causal Formation Gate Diagnostics

Adds `v1_formation_gates.csv` to preserve the physical chain:

`cloud exists -> finite-solar-disk direct-solar geometry -> Sun→CloudBase red-path resolution -> red light reaches CloudBase`.

Viewing/observer-path visibility is deliberately excluded from this table.
