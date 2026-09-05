# Taiwan Firecloud PhysicsCore V1.0-R4.2

## Shared Adaptive Horizontal Sampling
- 0–40 km: 5 km forecast/geometry sampling.
- 40–100 km: 10 km sampling.
- 100 km and beyond: 20 km sampling (including the legacy 100–440 km diagnostic range).
- One shared node contract drives route points, CloudScene input, Canvas candidates, SolarRay sampling, CASE archive, and later 2D/3D consumers.
- `sampling step != cloud horizontal thickness` is explicit in CASE provenance.

## Native 3D upstream cloud optical support
- Target-cloud COT is no longer counted as Sun→CloudBase path extinction; it remains a Canvas response property.
- A finite upstream cloud horizontal support interval is created only when vertically overlapping native-condensate optical evidence exists at the immediately adjacent sampled columns on both sides.
- Support is tagged `MULTICOLUMN_NATIVE_CONDENSATE_CONTINUITY` with MEDIUM confidence.
- R4.2 numerically integrates the G0 ray through that supported 3D cloud prism and derives `slant_path_km` and `slant_cloud_optical_depth`.
- Unresolved single-column/edge clouds remain `POTENTIAL_BLOCKER_HORIZONTAL_SUPPORT_UNKNOWN`; no sampling spacing is converted into cloud width.
- Multiple resolved upstream blockers sum their slant COT. Any unresolved blocker keeps total cloud-path tau Unknown.

## CASE additions
- `horizontal_sampling_profile.csv`
- `v1_cloud_horizontal_support.csv`
- `v1_ray_cloud_intersections.csv` adds support source/confidence, slant path, slant COT, and slant-optics status.
- `v1_spectral_optical_paths_550_750nm.csv` adds resolved upstream blocker counts and resolved upstream cloud tau.

## Scientific boundary
R4.2 still does not fabricate COT from RH/cloud fraction/base/top, and it does not fabricate precipitation optical depth. 550-nm gas spectroscopy remains fail-closed until a verified six-band LUT is available.
