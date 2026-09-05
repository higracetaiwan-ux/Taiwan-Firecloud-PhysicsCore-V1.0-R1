# Taiwan Firecloud PhysicsCore V1.0-R5.2 Release Notes

## Finite-Solar-Disk Penumbra + Red Illumination

R5.2 replaces any binary interpretation of the traditional Earth-shadow height with explicit finite-solar-disk transition geometry.

New diagnostics:
- `H_any_sun`: upper solar limb first visible (start of penumbra; `F_sun > 0`).
- `H_solar_center`: solar-disk center clears the geometric Earth limb. This is the traditional shadow-height diagnostic, not a Formation gate by itself.
- `H_full_solar_disk`: lower solar limb clears the Earth limb (`F_sun = 1`).
- `v1_earth_shadow_penumbra_matrix.csv`: core 0..-4 deg angles x 10/20/30/40 km transition heights.
- `v1_canvas_penumbra_red_illumination.csv`: actual Canvas cloud-base height, finite-disk `F_sun`, red-band path transmission and base illumination.

Formation remains causal: Cloud exists + finite solar-disk geometry + Sun->CloudBase spectral transmission. No fixed `effective red height` threshold is invented. Viewing remains separate.
