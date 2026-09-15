# Firecloud Ice Optics Portable V1.1 — Validation Report

## Artifact
- File: `Firecloud-Ice-Optics-Portable-V1.1-R5.7.41.3.4.10.11.1.zip`
- SHA256: `802d82b49cef4e20a4458bc50f063133a58b19fcfcb4e49941cc8ca16f7afd05`
- Byte size: `1466710`

## Validation result
**PASS — Portable Package Validation Gate**

### Package structure
- 10 required members present
- `manifest.json`
- `contract.json`
- `ice_optics_lut_v1.csv`
- `ice_optics_lut_v1.json`
- `source/source_manifest.json`
- `validation/reference_vectors.json`
- `validation/validatePackage.mjs`
- `windy/iceOpticsEvaluator.mjs`
- `windy/iceOpticsEvaluator.ts`
- `README_WINDY.md`

### Internal manifest integrity
- Every member SHA256 matches `manifest.json`
- Every member byte size matches `manifest.json`

### LUT integrity
- Rows: **30,618**
- Habits: **9**
- Roughness states: **3**
- Dmax nodes per habit/roughness: **189**
- Six-band groups: **5,103**
- Bands: **550 / 575 / 600 / 650 / 700 / 750 nm**
- Duplicate authoritative keys: **0**
- Incomplete six-band groups: **0**
- Primary size coordinate: `maximum_dimension_um`
- Effective radius is diagnostic/mapping metadata only

### CSV ↔ JSON parity
- All 30,618 records structurally consistent
- String fields: 0 mismatches
- Numeric differences only at floating serialization roundoff (~1e-12 or smaller)

### Evaluator validation
- Built-in Node validation: **PASS 12 vectors**
- Randomized Python ↔ JavaScript parity: **PASS 100 cases**
- TypeScript strict compile: **PASS**
- Exact Dmax lookup: covered
- Linear Dmax interpolation: covered
- Positive-IWP missing-Dmax fail-close: covered
- Exact-zero IWP semantics: covered
- Incomplete vertical-support fail-close: covered

## Science boundary
- `physics_promotion_allowed = false`
- This package certifies the authoritative Yang/Bi V2 six-band Dmax-first LUT and standalone evaluator only.
- It does **not** promote Ice Optics into Production Formation / Viewing / Twilight Glow.
- No r_eff → Dmax conversion is fabricated.
- Missing ≠ Clear ≠ Zero remains enforced.

## Next science gate
Proceed to Phase 2 only after this certification:
1. define/validate forecast microphysics → Dmax/PSD mapping,
2. habit-mixture strategy,
3. roughness strategy,
4. bulk ice optical properties,
5. only then evaluate production `IWP → tau_ice` coupling.
