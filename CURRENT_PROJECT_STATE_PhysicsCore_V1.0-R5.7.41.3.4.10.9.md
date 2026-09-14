# Taiwan Firecloud PhysicsCore — Current Project State

Current release: **V1.0-R5.7.41.3.4.10.9 — Viewing→Glow Gas Spectroscopy Cache Handoff**

Science baseline remains frozen at `R5.7.41.2_SHADOW_COT_AB_FROZEN`.

## Runtime roadmap status

- `.10.1` Observer Aerosol Numeric Route Context：FIELD PASS
- `.10.2` Molecular Numeric Route Context：FIELD PASS
- `.10.3` Observer Precipitation Horizontal-Support Ray Reuse：FIELD PASS
- `.10.4` Gas Spectroscopy State Memo：FIELD PASS
- `.10.5` Route Group Direct Reuse：science exactness PASS / runtime NOT FIELD PASS
- `.10.6` Cloud Numeric Route Context：FIELD PASS
- `.10.7` Viewing↔Glow Shared Hydrometeor Context：FIELD PASS
- `.10.8` Viewing→Glow Molecular Context Handoff：**FIELD PASS**（TWS091 2026-09-14 sunrise，Lookup Context Prep 6.647128 → 0.256652 s）
- `.10.9` Viewing→Glow Gas Spectroscopy Cache Handoff：REGRESSION PASS / FIELD TEST CANDIDATE

## `.10.9` purpose

Main Viewing `.10.4` spectroscopy memo already owns a content-scoped `gas_sigma_cache`. Twilight Glow Volume Assembly previously recalculated the same `_sigma_fast()` cross sections for O2/H2O/O3 × six bands. `.10.9` hands the exact Viewing cache and per-route LUT signature into Glow gas-species decomposition.

Cache key remains unchanged from `.10.4`:

`LUT content signature + gas + wavelength + exact T + exact P`

If the shared cache or route LUT signature is unavailable, Glow executes the original `_sigma_fast()` path.

## Baseline for next Field run

2026-09-14 sunrise TWS091 `.10.8`:
- Glow Lookup Context Prep：0.256652 s
- Glow Volume Assembly：4.542999 s
- Glow Observer Spectral：1.764785 s
- Glow Observer Precipitation：1.307537 s
- Glow total：10.252142 s

Primary `.10.9` Field gate：`TWILIGHT_GLOW_COMPONENT_VOLUME_ASSEMBLY` must materially decline from 4.542999 s; net Glow time must not regress.
