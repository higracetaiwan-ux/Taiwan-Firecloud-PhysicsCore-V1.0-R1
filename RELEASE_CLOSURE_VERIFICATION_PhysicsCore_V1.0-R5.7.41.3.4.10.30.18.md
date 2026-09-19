# Taiwan Firecloud PhysicsCore V1.0 — Release Closure Verification

## R5.7.41.3.4.10.30.18

**Result: QA PASS**

### Science freeze
- Science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`
- Formation / Viewing / Twilight Glow unchanged.
- Production Ice Optics remains fail-closed.

### Regression
- Step3Q lineage: `57/57 PASS`
- Full regression: `984/984 PASS`
- Failures: `0`
- Existing pandas FutureWarning: `1`
- Collected tests: `984`

### Step 3Q.18 gates
- `FU96_PRIMARY_0P700UM_SPECTRAL_BOUNDARY_PINNED=True`
- `RRTMG_BAND25_WITHIN_SINGLE_FU96_PRIMARY_BAND_QUALIFIED=True`
- `RRTMG_BAND24_STRADDLES_FU96_PRIMARY_0P700UM_BOUNDARY_QUALIFIED=True`
- `RRTMG_BAND24_FINAL_TABLE_INVERSE_REAVERAGING_NONUNIQUE_QUALIFIED=True`
- `RRTMG_BAND24_FINAL_TABLE_INVERSE_REAVERAGING_UNIQUE=False`
- `FINAL_TABLE_INVERSE_IDENTIFICATION_ALLOWED=False`
- `EXACT_FU96_BAND_WEIGHTING_AVAILABLE=False`
- `TAU_ICE_PRODUCTION_ALLOWED=False`
- `PRODUCTION_ICE_OPTICS_READY=False`

### Fresh-extract pre-closure
- Step3Q: `57/57 PASS`
- Test collection: `984`
- Evidence / gate / contract regeneration: `BYTE-EXACT PASS`

### Artifact SHA256
- evidence: `8ca8093973d164facfb850509cad6ec06c155d1716aaef3d2ace4976d97987c6`
- gate: `1d30d22e627d018e12f597ec76249a7dd2845fff0c42374f02e519961ff3377c`
- contract: `f2e3f7868e2cb6afd55500ef3dbd816757697b539139b546ecb49b1515720ec8`

Final ZIP CRC / fresh-extract verification is repeated after this report is embedded in the release package.
