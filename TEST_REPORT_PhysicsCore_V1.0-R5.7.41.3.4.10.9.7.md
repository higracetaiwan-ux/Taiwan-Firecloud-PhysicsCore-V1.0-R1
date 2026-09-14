# Test Report — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.9.7

## Working-tree regression

- Full pytest: **722/722 PASS**
- Warning: **1** existing pandas `FutureWarning` in `test_r5732_glow_observer_aerosol_coverage.py`
- New `.10.9.7` targeted tests: **4/4 PASS**
- Adjacent CAMS/GFS regression subset: **31/31 PASS**

## New contracts tested

1. Complete CAMS scattering AOD550/645/670/800 skips dedicated `SPECTRAL_COLUMN_AOD` provider request.
2. Incomplete scattering AOD automatically falls back to dedicated spectral request.
3. GFS merge preserves existing provider precedence and cloud-fraction percent conversion without pandas `PerformanceWarning`.
4. Analysis Integrity recognizes only explicit `AEROSOL_SCATTERING_COLUMN_PROPERTIES` → `SPECTRAL_COLUMN_AOD` exact-reuse provenance.

## Frozen science audit

The following files are byte-identical to `.10.9.6`:

`formation.py`, `viewing.py`, `viewing_spectral.py`, `twilight_glow.py`, `gas_rt.py`, `cloud_optics.py`, `config.py`, `red_light_availability.py`, `photography_decision.py`, `native_cloud.py`, `formation_gates.py`, `formation_prerequisites.py`, `spectral_rt.py`, `spectral_color.py`, `illumination.py`, `optical_path.py`.

## Fresh-extract / FULL-CLEAN

- final fresh-extract pytest: **722/722 PASS**
- FULL-CLEAN entries: **842**
- cache/pyc contamination: **0**
- warning: 1 existing pandas `FutureWarning`

## Field proxy

TWS106 `.10.9.6` CAMS audit:
- dedicated `SPECTRAL_COLUMN_AOD`: 47.275 s
- `AEROSOL_SCATTERING_COLUMN_PROPERTIES`: same CAMS date/time/lead/area and includes native AOD550/645/670/800
- exported CAMS route snapshots: 2691/2691 rows have all four AOD source columns

This proves reuse eligibility for that CASE; actual `.10.9.7` wall-clock improvement requires a new Field run.
