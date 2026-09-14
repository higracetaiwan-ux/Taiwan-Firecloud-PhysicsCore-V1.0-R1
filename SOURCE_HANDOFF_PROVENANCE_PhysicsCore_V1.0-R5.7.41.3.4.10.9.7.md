# Source Handoff Provenance — V1.0-R5.7.41.3.4.10.9.7

Base release: `V1.0-R5.7.41.3.4.10.9.6`.

Changed runtime/orchestration files:
- `firecloud/providers/cams_native.py`: exact scattering→spectral AOD reuse with fallback.
- `firecloud/providers/gfs_native.py`: batch canonical-column construction / defragmentation only.
- `firecloud/case_integrity.py`: exact-reuse provenance Integrity check.
- `firecloud/model.py`: operator progress wording for exact reuse.
- `firecloud/__init__.py`: version bump.
- tests/docs updated for `.10.9.7`.

Frozen science source audit: `formation.py`, `viewing.py`, `viewing_spectral.py`, `twilight_glow.py`, `gas_rt.py`, `cloud_optics.py`, `config.py`, `red_light_availability.py`, `photography_decision.py`, `native_cloud.py`, `formation_gates.py`, `formation_prerequisites.py`, `spectral_rt.py`, `spectral_color.py`, `illumination.py`, `optical_path.py` are byte-identical to `.10.9.6`.
