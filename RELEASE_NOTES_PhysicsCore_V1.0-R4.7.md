# Taiwan Firecloud PhysicsCore V1.0-R4.7

## Six-band Formation Prerequisite Integration

- Added `v1_six_band_spectroscopy_readiness.csv`, auditing H2O/O2/O3 readiness at 550/575/600/650/700/750 nm across the required T/P grid. Missing 550 nm spectroscopy remains fail-closed; no interpolation from 575/600 nm is permitted.
- Added the formal `PrecipitationVolume` contract and expanded precipitation-path evidence to accept only explicit path/3-D hydrometeor optical-depth inputs. Surface rain rate is never converted to `tau_precip`.
- Added `v1_precipitation_path_evidence.csv` to CASE archives so precipitation-path uncertainty is auditable independently of Formation.
- Preserved the R4.6 Target Canvas optical-evidence strategy: cloud-fraction geometry can remain a Canvas while COT stays unresolved; no cloud-fraction/RH-to-COT fabrication.
- R4.7 does not claim `READY_FOR_SIX_BAND_FORMATION` unless target Canvas optics, 550 nm gas spectroscopy, precipitation-path optics and a full six-band path are all evidenced.
