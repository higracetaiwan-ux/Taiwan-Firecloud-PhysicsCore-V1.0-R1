# Taiwan Firecloud PhysicsCore V1.0-R3.1

Foundation fix after the 2026-09-05 R3 regression CASE.

- GEOMETRY_ONLY cloud evidence can no longer become tau_cloud=0 from a legacy transmission=1 voxel.
- Ray intersections with unresolved cloud optics are labelled POTENTIAL_BLOCKER_OPTICS_UNKNOWN.
- Native single-level cloud occupancy now uses native half-level vertical support rather than zero thickness.
- Six-band HITRAN builder/bootstrap target expanded to 550/575/600/650/700/750 nm and 535–765 nm local tables. Existing embedded LUT remains fail-closed at 550 until rebuilt/imported; no 550 gas value is fabricated.
- Precipitation path branch connected fail-closed. Surface rain rate never becomes 3-D optical depth.
- Gas-profile and aerosol-spectral derivations receive per-run/lead caches; existing CAMS persistent cache path is retained.
- No Formation scoring changes. No legacy fixed REZ physics is reintroduced.
