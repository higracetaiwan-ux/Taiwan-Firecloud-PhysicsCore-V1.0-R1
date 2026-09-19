# Taiwan Firecloud PhysicsCore V1.0 — FIELD Validation

## R5.7.41.3.4.10.30.18 — TWS100 — 2026-09-20 sunrise

**Result: FIELD FAIL**

### 1. Runtime identity
- Program version: `1.0.0-R5.7.41.3.4.10.30.18`
- Science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`
- Site: `TWS100 合歡山北峰`
- Event: `2026-09-20 sunrise`
- Timezone: `Asia/Taipei`
- Run mode: `WARM_PRODUCTION`
- Analysis job ID: `a17ea93e-630d-42ab-9573-26eb475b2367`
- Worker status: `COMPLETED`
- Worker exit code: `0`
- Worker traceback/error: empty

### 2. CASE archive integrity
- CASE ZIP members: `201`
- ZIP CRC: `PASS`
- CASE SHA256: `f1d3b03853c9c8b26b4420e21ef30b834fa3a3becb10e5b031a334da2ee0d876`
- `case_archive_manifest.csv`: `199/199` members present
- Independent SHA256 recomputation: `199/199 PASS`
- Independent byte-size recomputation: `199/199 PASS`

However:
- `case_integrity_audit.csv`: `138 PASS / 2 FAIL`
- `analysis_integrity_audit.csv`: `124 PASS / 7 WARN / 4 ALLOWED_EMPTY / 3 NOT_APPLICABLE / 2 FAIL`

The two case-level failures are propagated from analysis integrity:
- `ANALYSIS_INTEGRITY_PROPAGATED = FAIL`
- `CASE_ARCHIVE_INTEGRITY_OVERALL = FAIL`

### 3. Analysis failure root cause
The hard analysis failure is:

`CAMS_AEROSOL_SPECTRAL_PAYLOAD_VALIDITY = FAIL`

Observed:
`0.0`

Expected:
`>=0.95 rows with numeric spectral AOD payload`

The corresponding CAMS temporal provenance audit also reports:
- exact = `0.000000`
- real bounded fallback = `0.000000`
- missing = `1.000000`

This is a real Missing state and was correctly preserved as Missing. It was not converted to Clear or Zero.

### 4. CAMS request failure pattern
`cams_request_audit.csv` contains six request roles.

Successful:
- `O3_PRESSURE_LEVEL`: `OK`
- `O3_NEAR_SURFACE_MODEL_LEVEL_137`: `OK`

Deferred timeout:
- `PRESSURE_LEVEL_CHEMISTRY_OPTICS_BUNDLE`: `TIMEOUT_DEFERRED`
- `NATIVE_AEROSOL_532NM_PRESSURE_LEVEL`: `TIMEOUT_DEFERRED`
- `AEROSOL_SCATTERING_COLUMN_PROPERTIES`: `TIMEOUT_DEFERRED`
- `SPECTRAL_COLUMN_AOD`: `TIMEOUT_DEFERRED`

All four deferred requests report:

`CAMS_ADS_RUNNING_GRACE_EXCEEDED`

Representative remote running durations were approximately 134–138 s before the running-grace contract fired.

This explains why the aerosol spectral payload was unavailable.

### 5. Step 3Q.18 release ↔ FIELD byte-exact closure
Despite the CAMS runtime failure, all Step 3Q.18 provenance artifacts are valid and byte-exact against the verified `.10.30.18 FULL-CLEAN` release.

| Artifact | SHA256 | Result |
|---|---|---|
| `ice_microphysics_fu96_rrtmg_band_weighting_provenance_evidence.csv` | `8ca8093973d164facfb850509cad6ec06c155d1716aaef3d2ace4976d97987c6` | BYTE-EXACT PASS |
| `ice_microphysics_fu96_rrtmg_band_weighting_provenance_gate.csv` | `1d30d22e627d018e12f597ec76249a7dd2845fff0c42374f02e519961ff3377c` | BYTE-EXACT PASS |
| `ice_microphysics_fu96_rrtmg_band_weighting_provenance_contract.json` | `f2e3f7868e2cb6afd55500ef3dbd816757697b539139b546ecb49b1515720ec8` | BYTE-EXACT PASS |

### 6. Step 3Q.18 runtime provenance gate
The new Step 3Q.18 provenance conclusions remain correct in the FIELD runtime:

- `FU96_PRIMARY_0P700UM_SPECTRAL_BOUNDARY_PINNED=True`
- `RRTMG_BAND25_WITHIN_SINGLE_FU96_PRIMARY_BAND_QUALIFIED=True`
- `RRTMG_BAND24_STRADDLES_FU96_PRIMARY_0P700UM_BOUNDARY_QUALIFIED=True`
- `RRTMG_BAND24_FINAL_TABLE_INVERSE_REAVERAGING_NONUNIQUE_QUALIFIED=True`
- `RRTMG_BAND24_FINAL_TABLE_INVERSE_REAVERAGING_UNIQUE=False`
- `FINAL_TABLE_INVERSE_IDENTIFICATION_ALLOWED=False`

Production guards remain closed:
- `PREAVERAGING_SPECTRAL_SAMPLES_RECOVERED=False`
- `RRTM_SW_PREAVERAGING_GENERATOR_RECOVERED=False`
- `RRTMG_BAND24_EXACT_REPRODUCTION_PASS=False`
- `RRTMG_BAND25_EXACT_REPRODUCTION_PASS=False`
- `TAU_ICE_PRODUCTION_ALLOWED=False`
- `PRODUCTION_ICE_OPTICS_READY=False`
- `physics_promotion_allowed=False`

Therefore the FIELD failure is **not** caused by Step 3Q.18 provenance logic.

### 7. Physical outcome
`summary.csv` contains 13 solar-angle rows from `−6°` through `0°`.

For all 13 rows:
- `core_score_eligible=False`
- `primary_canvas_state=ABSENT`
- `extended_canvas_state=ABSENT`

However, because CAMS aerosol spectral evidence is Missing and the analysis audit contains a hard FAIL, this no-Canvas physical outcome cannot be used to declare a formal FIELD PASS for `.10.30.18`.

### 8. Runtime performance
- `GFS_PREFETCH_TOTAL`: `14.258 s`
- `CAMS_PREFETCH_TOTAL`: `656.466 s`
- `ALL_ANGLES_PHYSICS_TOTAL`: `212.712 s`
- `TOTAL_ANALYSIS_CORE`: `1048.896 s`
- `TOTAL_TO_CASE_ARCHIVE`: `1105.867 s`
- Worker elapsed: `1135.642 s`

The dominant regression is CAMS prefetch time, driven by the four deferred ADS requests.

### 9. Formal conclusion
`R5.7.41.3.4.10.30.18` does **not** satisfy the formal FIELD gate for TWS100 / 2026-09-20 sunrise.

**Formal status: `R5.7.41.3.4.10.30.18 FIELD FAIL — CAMS_AEROSOL_SPECTRAL_PAYLOAD_VALIDITY`**

Important interpretation:
- The release package and Step 3Q.18 provenance artifacts are intact.
- The new Band-24 non-unique inverse re-averaging gate behaves correctly.
- The failure is a runtime data-acquisition/completeness failure in CAMS aerosol spectral evidence.
- Missing remained Missing; no silent substitution occurred.
- Frozen science remains unchanged.

The current formal FIELD baseline therefore remains:

`R5.7.41.3.4.10.30.17 FIELD PASS`

Recommended next engineering action:
1. preserve the current `.10.30.18` provenance changes unchanged;
2. address CAMS running-grace / stateful reattachment behavior for deferred aerosol requests;
3. rerun `.10.30.18` FIELD on TWS100 or another site;
4. only declare `.10.30.18 FIELD PASS` after `CAMS_AEROSOL_SPECTRAL_PAYLOAD_VALIDITY` and overall analysis/case integrity both pass.
