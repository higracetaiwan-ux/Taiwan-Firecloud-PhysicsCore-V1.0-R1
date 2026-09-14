# Source Handoff Provenance — V1.0-R5.7.41.3.4.10.9.6

Base: `V1.0-R5.7.41.3.4.10.9.5`

## Byte-identical Frozen science sources

- `firecloud/formation.py`
- `firecloud/viewing.py`
- `firecloud/viewing_spectral.py`
- `firecloud/twilight_glow.py`
- `firecloud/gas_rt.py`
- `firecloud/cloud_optics.py`
- `firecloud/config.py`
- `firecloud/red_light_availability.py`
- `firecloud/photography_decision.py`
- `firecloud/native_cloud.py`
- `firecloud/formation_gates.py`
- `firecloud/formation_prerequisites.py`
- `firecloud/spectral_rt.py`
- `firecloud/spectral_color.py`
- `firecloud/illumination.py`
- `firecloud/optical_path.py`

## Changed orchestration / diagnostics

- `firecloud/model.py`: attach GFS provider-valid-time provenance to native columns; collect source-attribution diagnostics; no Physics formula changes.
- `firecloud/observer_environment_timeline.py`: provider-valid-time matching + T−180→T+60 diagnostic window.
- `firecloud/gfs_native_nearfield_source_diagnostic.py`: new diagnostic-only module.
- `firecloud/case_integrity.py`: evidence-chain checks only.
- `app.py`: CASE export members only.
- tests/docs/version metadata.

No Frozen Formation / Viewing / Glow / COT / six-band / Earth-shadow decision rule was changed.
