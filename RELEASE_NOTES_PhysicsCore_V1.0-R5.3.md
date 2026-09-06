# Taiwan Firecloud PhysicsCore V1.0-R5.3 Release Notes

## Illuminated Canvas Retreat

R5.3 adds an explicit outward-retreat diagnostic for sunset firecloud illumination while preserving the frozen separation between finite-solar-disk geometry and spectral radiative transfer.

### New CASE tables
- `v1_illuminated_canvas_retreat.csv`: actual Canvas retreat by solar altitude. Geometry uses only `F_sun`; physical-red retreat is populated only where Sun→CloudBase spectral RT and red CloudBase illumination are resolved.
- `v1_reference_canvas_retreat.csv`: geometry-only reference for cloud bases 4/5/6/8/10/12/15 km across the shared 0–100 km adaptive distance grid. This permits diagnosis of 4–8 km cloud retreat even when a particular forecast CASE lacks those layers.

### Frozen semantics
- Near-cloud fade / outward retreat is an illumination-envelope movement, not cloud motion.
- Geometry access does not imply firecloud formation.
- Penumbra geometry and spectral RT remain separate and are combined only at CloudBase illumination.
- No arbitrary effective-red-height threshold is introduced.

### Repository hygiene
- Added `.gitattributes` to normalize source/text files to LF for GitHub/Linux deployment while keeping binary assets binary.
