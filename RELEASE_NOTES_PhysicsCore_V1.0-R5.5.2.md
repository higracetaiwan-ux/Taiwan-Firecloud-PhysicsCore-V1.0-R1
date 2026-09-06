# Taiwan Firecloud PhysicsCore V1.0-R5.5.2 Release Notes

## Scope

R5.5.2 fixes the two blockers demonstrated by the 2026-09-06 sunset R5.5.1 CASE:

1. DWD ICON Global native model-level QC/QI could be downloaded but the unstructured GRIB decoder attempted to read unavailable `latitudes` / `longitudes` keys and failed.
2. Sun→CloudBase rays could intersect forecast cloud geometry whose primary CloudLayer COT was unresolved, leaving the upstream cloud optical component unresolved even when a forecast-native secondary optical provider could supply COT.

No Penumbra Geometry thresholds, six-band wavelengths, Formation dimensions, Canvas Suitability thresholds, or Viewing/Glow logic are changed in this release.

## 1. DWD ICON Global unstructured-grid decoder

### Root cause

ICON Global GRIB is distributed on the native unstructured triangular grid. Horizontal grid geometry is not embedded as per-cell latitude/longitude arrays in the forecast GRIB. DWD supplies separate ICON grid/remap resources.

### R5.5.2 implementation

- Uses the official DWD `ICON_GLOBAL2WORLD_025_EASY.tar.bz2` bundle.
- Extracts `weights_icogl2world_025.nc` only; the ~938 MB full ICON grid file is not required for route-point nearest-neighbour lookup.
- Reads CDO `src_address` / `dst_address` arrays and builds a cached destination→native-source lookup.
- Uses the documented 0.25° target grid (`1440 × 721`, lon 0..359.75, lat -90..90) to map route points to target cells.
- ecCodes reads only the native GRIB `values` array; native source addresses index those values directly.
- The route→source map is resolved once and cached before QC/QI downloads.
- If grid mapping fails, the ICON branch exits immediately rather than issuing hundreds of doomed field requests.

### Audit state changes

New/clarified states include:

- `GRID_MAPPING_READY`
- `GRID_MAPPING_CACHE_HIT`
- `GRID_MAPPING_FAILED`
- `FIELD_DECODE_FAILED`
- `NATIVE_MICROPHYSICS_UNRESOLVED`
- `NATIVE_MICROPHYSICS_PARTIAL_UNRESOLVED`
- `ZERO_CONDENSATE`
- `POSITIVE_CONDENSATE`

A decode/mapping failure can no longer collapse into the semantic state "native microphysics present but condensate zero".

## 2. Sun→CloudBase upstream cloud optical bridge

R5.5.2 adds a path-only secondary optical view.

Priority for each CloudLayer used as an upstream blocker:

1. Primary CloudLayer native COT, when resolved.
2. Exact forecast-native secondary optics (IFS / DWD ICON) at the same direction and route distance, with sufficient vertical overlap.
3. Otherwise remain unresolved.

Rules:

- No Cloud Fraction → COT.
- No RH → COT.
- No geometry → COT.
- No satellite observation as forecast input.
- Secondary COT never rewrites the frozen `CloudScene` object.
- Secondary path evidence never automatically becomes target Canvas Optical Suitability evidence.
- Slant optical depth is resolved only when adjacent optical support exists on both sides; the sampling interval is not cloud width.
- Partial vertical coverage below the required threshold remains unresolved.

New ray-intersection diagnostics include:

- `path_layer_vertical_cot`
- `path_optical_evidence_source`
- `path_optical_evidence_status`
- `path_optical_vertical_coverage_fraction`
- `path_secondary_record_count`
- `RESOLVED_SECONDARY_NATIVE_FORECAST_SLANT_RT`

## 3. Frozen separation retained

R5.5.2 continues to enforce:

`Penumbra Geometry ≠ Spectral RT ≠ Target Cloud Optical Response`

and:

`Missing ≠ Zero ≠ Clear`

The secondary bridge can close only `tau_cloud` on the Sun→CloudBase path. Missing gas, aerosol, precipitation or any unresolved cloud blocker remains Missing and prevents false `FULL_OPTICAL_PATH` closure.

## 4. Validation

Full test suite after R5.5.2 changes:

- **275 passed**
- **0 failed**

New R5.5.2 tests verify:

- CDO source-address conversion from 1-based to 0-based indices.
- 0.25° target-grid address calculation.
- ICON GRIB decoding reads `values` only and does not request `latitudes/longitudes`.
- Grid mapping failure aborts before mass field downloads.
- Exact secondary forecast-native COT can resolve an upstream slant cloud optical depth.
- The upstream bridge does not mutate CloudScene and does not fabricate missing GAS/aerosol/precipitation RT components.

## 5. Runtime note

The packaged implementation is network-capable in deployment. The build/test environment used for this release could inspect the official DWD documentation through web retrieval but did not permit direct runtime DNS/network access from the local test container, so live DWD OpenData download execution was not performed during packaging. The decoder and remap logic are covered by deterministic unit tests and should be verified with the next archived CASE after deployment.
