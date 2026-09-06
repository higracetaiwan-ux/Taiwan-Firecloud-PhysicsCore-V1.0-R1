# Taiwan Firecloud PhysicsCore V1.0-R5.7.5

## Provider Data Sharing / Decoded Cache Performance

R5.7.5 is an operational performance release. It does **not** change Formation, Viewing, Photography Decision, Penumbra Geometry, six-band wavelengths, optical thresholds, or Missing semantics.

### Why this release exists
A 2026-09-06 R5.7.2 CASE showed that most provider network requests were already cache hits, yet substantial time remained because cached GRIB files were repeatedly decoded and some provider state was rebuilt for every analysis/process.

Observed cached CASE evidence:
- GFS: one request state, raw cache used.
- Open-Meteo: 7/7 route batches cache hits.
- CAMS: 3/3 roles raw-cache hits, but the three roles still consumed ~12 s because each external worker opened/decoded cached GRIB.
- DWD ICON: 1,125 audit rows, 1,098 marked cache hit; this exposed repeated cache/decode/reconstruction bookkeeping across candidate times.

### Changes
1. **CAMS persistent decoded-route cache**
   - Cache key = role + CAMS run/lead + exact route signature + cache schema.
   - A decoded-cache hit skips external worker startup and GRIB decode entirely.
   - Raw GRIB cache remains the fallback underneath.
   - No synthetic O3/aerosol values are introduced.

2. **GFS persistent decoded-route cache**
   - After the NOMADS subset is decoded once, the route DataFrame is persisted next to the raw provider cache.
   - Later analyses sharing the same raw GRIB + exact route signature can skip ecCodes route decoding.

3. **DWD ICON persistent secondary-optics cache**
   - Persist the decoded/reconstructed secondary target optics, not only individual raw ICON field files.
   - Cache key includes run/lead, route geometry, model-level set, **surface-pressure anchor and surface-elevation anchor** so vertical reconstruction is never reused across incompatible surface states.
   - Runtime/persistent decoded-cache hits now emit a compact audit row instead of replaying hundreds of old `FIELD_FETCH` cache-hit rows.

4. **API efficiency audit**
   - CASE adds `api_efficiency_audit.csv` summarizing network requests, raw cache hits, decoded cache hits and failures by provider.

### Scientific invariants
- Missing != Clear != Zero.
- Cloud Fraction != COT; RH != COT.
- Formation remains Sun→CloudBase.
- Viewing remains Cloud→Observer.
- Photography Decision remains an outer layer.
- 550/575/600/650/700/750 nm remain separate throughout the six-band chain.
- Provider caches only reuse data derived from the same explicit source state; they do not create or interpolate missing optical evidence.
