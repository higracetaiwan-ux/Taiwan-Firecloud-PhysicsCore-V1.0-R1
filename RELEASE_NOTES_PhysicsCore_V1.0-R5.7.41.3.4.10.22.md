# RELEASE NOTES — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.22

## R5.7.41.3.4.10.22 — Step 3I Wyser Population + Yang/Bi Optical-Kernel Bridge

### Added

- Diagnostic hybrid bridge on the Step 3H-qualified maximum-dimension coordinate.
- Explicit dual-mass contract:
  - Wyser Eq.(6) mass → PSD/IWC population normalization.
  - Yang/Bi `rho_ice*V` mass → compact-LUT `k_ext` to single-particle `C_ext` inversion only.
- Yang/Bi V2 `single_column/Rough000` reference-kernel reconstruction over 10–1000 µm: 109 sizes × six wavelengths = 654 rows.
- Full-domain geometry/area/volume/mass non-equivalence diagnostics.
- Step 3I evidence/gate/contract CASE handoff and integrity gates.

### Frozen / not promoted

- No direct shape/area/volume-mass equivalence claim.
- No hidden area or mass correction.
- No runtime habit or roughness default.
- No bulk PSD integration promotion.
- No production `tau_ice`.
- No GFSv16 Dmax mapping.
- No Formation/Viewing/Twilight Glow science change.

### Gate state

`WYSER_YANG_HYBRID_POPULATION_BRIDGE_NUMERIC_READY_SCIENTIFIC_PROMOTION_BLOCKED`

### Validation

- Focused Step 3G–3I: 33 PASS.
- Full regression: 864 PASS, 1 existing warning.
- FIELD validation pending.
