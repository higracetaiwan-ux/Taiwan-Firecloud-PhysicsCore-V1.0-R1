# Taiwan Firecloud PhysicsCore V1.0

**Current checkpoint: V1.0-R4.1 — Native Cloud Optical Evidence Bridge.**

R4.1 connects native GFS liquid/ice condensate + native thermodynamic levels to CloudLayer optical evidence without using RH, cloud fraction, cloud base/top, or display voxels to fabricate COT. When native condensate is unavailable the layer remains `GEOMETRY_ONLY` and Formation remains uncertain.

Key boundary: target-cloud vertical COT can be derived from native condensate using an explicit geometric-optics model with assumed effective radii. Upstream slant cloud optical depth is **not** fabricated from isolated route columns; it remains unresolved until native horizontal/3-D support is available.

Six-band and Missing semantics from R3.x/R4 remain unchanged. 550-nm gas spectroscopy remains fail-closed until a verified six-band gas LUT is installed.

See `RELEASE_NOTES_PhysicsCore_V1.0-R4.1.md`.
