# Taiwan Firecloud PhysicsCore V1.0 — Release Closure Verification

## R5.7.41.3.4.10.30.21

**Step 3Q.21 — Band25 Historical Source-Domain / Runtime-Weight Scope Qualification + CAMS Bounded Reattach Observation Window**

### Closure gates
- Frozen science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`
- Latest FIELD baseline: `R5.7.41.3.4.10.30.20 FIELD PASS`
- Step3Q.21 / CAMS targeted: `12/12 PASS`
- Step3Q lineage: `76/76 PASS`
- Full regression: `1003/1003 PASS`（12 批完整覆蓋 1003-test collection）
- Step3Q.21 verifier: PASS
- Release evidence/gate/contract regenerated from current code.
- Production promotion remains fail-close.

### Qualified increment
- Fu96-lineage source wavelength sample count: `200` qualified
- exact 200 wavelength node coordinates recovered: `False`
- six solar primary bands qualified: `True`
- AER current RRTMG_SW 3-µm Dge runtime linear interpolation pinned: `True`
- runtime Dge interpolation is historical spectral pre-averaging: `False`
- Band25 runtime g-point reduction scope qualified: `True`
- runtime `rwgt` is historical cloud pre-averaging solar vector: `False`
- runtime `sfluxref` reduction proves historical cloud weighting: `False`
- exact Band25 reproduction: `False`

### CAMS runtime closure
- initial 210 s deadline → default reattach observation `73.5 s`
- initial 90 s deadline → default reattach observation `31.5 s`
- same request-ID reattach preserved
- reattach-only preserved
- fresh submit forbidden
- second timeout remains Missing / fail-close
- adaptive and serial scheduler targeted tests PASS

### Fail-close
- `FU96_LINEAGE_EXACT_200_WAVELENGTH_NODE_GRID_RECOVERED=False`
- `RRTMG_FINE_SPECTRAL_GRID_REALIZATION_RECOVERED=False`
- `RRTMG_BAND25_HISTORICAL_INTRABAND_INPUT_BUNDLE_COMPLETE=False`
- `RRTMG_BAND24_EXACT_REPRODUCTION_PASS=False`
- `RRTMG_BAND25_EXACT_REPRODUCTION_PASS=False`
- `EXACT_FU96_BAND_WEIGHTING_AVAILABLE=False`
- `TAU_ICE_PRODUCTION_ALLOWED=False`
- `PRODUCTION_ICE_OPTICS_READY=False`
- `physics_promotion_allowed=False`

Step 3R remains blocked.

### Release artifact SHA256
- evidence: `f43ba4fa7dcf869fcc18eccadec105f3f52eb9239f62d236fa38ec6767d426ad`
- gate: `7a873a8877ce00b3764632fe863cbbd093cb20fb99ab677b8e44f64ba2fceeda`
- contract: `bc0f646466c5c97ae693b84dbccc43e54564fa7b0a1ea99796993b60dfe5de18`

### PRE-CLOSURE packaging verification
- ZIP file members: `1292`
- ZIP CRC: PASS
- cache / pyc entries: `0`
- fresh-extract Step3Q.21 verifier: PASS
- fresh-extract Step3Q lineage: `76/76 PASS`
- fresh-extract collection: `1003 tests`
- fresh-extract release evidence/gate/contract regeneration: `BYTE-EXACT PASS`

### FIELD status
`.10.30.21` 尚未 FIELD。這一版的 Band25 變更是 provenance/scope gate；CAMS reattach runtime policy 有 production-adjacent timing change，因此下一次 FIELD CASE 應重點觀察：若再次出現 `TIMEOUT_DEFERRED`，確認 `deferred_reattach_deadline_seconds` 實際縮短、仍沿用 original ADS request ID，且不產生 fresh duplicate submit。最新正式 FIELD baseline 保持 `.10.30.20 FIELD PASS`。
