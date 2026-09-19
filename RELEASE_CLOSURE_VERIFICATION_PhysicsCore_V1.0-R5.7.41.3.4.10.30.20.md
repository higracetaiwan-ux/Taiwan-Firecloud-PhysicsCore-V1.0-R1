# Taiwan Firecloud PhysicsCore V1.0 — Release Closure Verification

## R5.7.41.3.4.10.30.20

**Step 3Q.20 — Band25 Forward-Reproduction Harness + Contract Consistency Closure**

### Closure gates
- Frozen science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`
- New Step3Q.20 tests: `4/4 PASS`
- Step3Q lineage: `70/70 PASS`
- Full regression: `997/997 PASS`（分四段完整覆蓋 997-test collection）
- Band25 verifier: PASS
- Release evidence/gate/contract regenerated from current code.
- Production promotion remains fail-close.

### Qualified increment
- Band25 pinned reference grid: `46 nodes / Dge 5–140 µm / 3 µm step`
- Executable Band25 forward-reproduction negative-control harness: `True`
- Direct-primary residual topology qualified: `True`
- Serialized Fu96 linear/log co-albedo equations retain `beta_lambda`: `True`
- Historical Band25 intra-band input bundle complete: `False`
- Exact Band25 reproduction: `False`

### Fail-close
- `RRTMG_FINE_SPECTRAL_GRID_REALIZATION_RECOVERED=False`
- `PREAVERAGING_SPECTRAL_SAMPLES_RECOVERED=False`
- `EXACT_HISTORICAL_SOLAR_SPECTRUM_AND_WEIGHTS_RECOVERED=False`
- `RRTMG_BAND24_EXACT_REPRODUCTION_PASS=False`
- `RRTMG_BAND25_EXACT_REPRODUCTION_PASS=False`
- `EXACT_FU96_BAND_WEIGHTING_AVAILABLE=False`
- `TAU_ICE_PRODUCTION_ALLOWED=False`
- `PRODUCTION_ICE_OPTICS_READY=False`
- `physics_promotion_allowed=False`

Step 3R remains blocked.

### Packaging verification
- PRE-CLOSURE ZIP members: `1310`
- PRE-CLOSURE ZIP CRC: PASS
- PRE-CLOSURE cache / pyc entries: `0`
- PRE-CLOSURE fresh-extract Band25 verifier: PASS
- PRE-CLOSURE fresh-extract Step3Q lineage: `70/70 PASS`
- PRE-CLOSURE fresh-extract collection: `997 tests`
- PRE-CLOSURE release evidence/gate/contract regeneration: `BYTE-EXACT PASS`
- evidence SHA256: `00f5b65bdc64c2c44f93752a45df3f36970e42e8a1d82ed6939ce32e73d38969`
- gate SHA256: `13bc95aceac92239e7f89682e572f776d5a0cbe2a35e15683074f472887e3636`
- contract SHA256: `cbfdf092aa67f453b1385f6af91d29f328881082ccf087d7074c05bc19763199`

### FIELD status
`.10.30.20` 尚未執行 FIELD CASE；最新正式 FIELD baseline 保持 `R5.7.41.3.4.10.30.18.2 FIELD PASS`。本版沒有改動 production science/runtime decision path，因此不以 FIELD 未執行作為 QA release blocker。
