# Taiwan Firecloud PhysicsCore — FIELD Validation Closure

## Release
`V1.0-R5.7.41.3.4.10.30.9`

Science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`

## FIELD Case
- Site: `TWS001` 象山六巨石（台北市）
- Event: `2026-09-19 sunset`
- Program version: `1.0.0-R5.7.41.3.4.10.30.9`
- Analysis run mode: `WARM_PRODUCTION`
- GFS run: `2026-09-18T18:00:00+00:00`, forecast hour `16`
- CASE SHA256: `44a740c26463357ea96483b18057a515003945b67ee50c6fbed2890080b8238e`

## CASE Integrity
- ZIP members: **201**
- ZIP CRC: **PASS**
- cache / pyc artifacts in CASE: **0**
- `case_archive_manifest.csv`: **199/199 present**
- Manifest SHA256 verification: **199/199 PASS**
- Manifest byte-size verification: **199/199 PASS**
- `analysis_integrity_audit.csv`: **148/148 PASS**
- `case_integrity_audit.csv`: **140/140 PASS**

## Step 3Q.9 CASE ↔ Release Byte-Exact Verification
- evidence SHA256: `6d8539c8199beaafd23e6c0ecd32af69707178e129dc945d190359befe4c4069` — **BYTE-EXACT PASS**
- gate SHA256: `8a258604e710b2ddae2fe975201ff33c17a410cc9ea9662726c719bfb34dc086` — **BYTE-EXACT PASS**
- contract SHA256: `a0d35a7bd41c4473280cda69482c00de6c9f96160ab1808c8390e48d1a2c8f9f` — **BYTE-EXACT PASS**

Contract: `FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_9`

Qualification state:
`PASS_FAIL_CLOSED_V25_MIRROR_TIME_AND_RUNTIME_SOLAR_CONTEXT_QUALIFIED_PREAVERAGING_GENERATOR_UNRECOVERED`

## CAMS Runtime
- CAMS worker checkpoint: **COMPLETED**
- CAMS request-audit rows: **6**
- Fresh provider successes: **3**
- Exact-source reuse rows: **3**
- Request errors: **0**
- O3 payload validity: **PASS**
- Spectral aerosol payload validity: **PASS**
- Pressure-level exact-bundle reuse provenance: **PASS**
- Spectral AOD exact-source reuse provenance: **PASS**
- Post-success download recovery telemetry: **PASS**

## Production Ice Optics Guard
Fail-close remains intact:
- `RRTM_SW_PREAVERAGING_GENERATOR_RECOVERED=False`
- `EXACT_FU96_BAND_WEIGHTING_AVAILABLE=False`
- `RRTMG_BAND24_EXACT_REPRODUCTION_PASS=False`
- `RRTMG_BAND25_EXACT_REPRODUCTION_PASS=False`
- `INDEPENDENT_SSA_VALIDATION_PASS=False`
- `INDEPENDENT_ASYMMETRY_VALIDATION_PASS=False`
- `FULL_SIX_BAND_LIKE_FOR_LIKE_OPTICAL_VALIDATION_PASS=False`
- `TAU_ICE_PRODUCTION_ALLOWED=False`
- `PRODUCTION_ICE_OPTICS_READY=False`
- `physics_promotion_allowed=False`

## Runtime
- Analysis core: **380.464 s**
- Full runtime trace to final completion: **433.481 s**
- Final runtime stage: `分析完成。` / `COMPLETED` / progress `1.0`

## Decision

**FIELD PASS**

`R5.7.41.3.4.10.30.9 FIELD PASS` is now the latest formal FIELD engineering/provenance baseline.

The frozen science baseline remains `R5.7.41.2_SHADOW_COT_AB_FROZEN`. No Formation, Viewing, Twilight Glow, Canvas, Corridor/REZ, Earth Shadow, COT, or production Ice Optics science rule is changed by this FIELD closure.

Step 3R remains blocked until authoritative historical generator/equivalent archival evidence can deterministically reproduce archived band 24/25 tables.
