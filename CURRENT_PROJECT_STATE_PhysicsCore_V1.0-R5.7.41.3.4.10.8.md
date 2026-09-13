# Taiwan Firecloud PhysicsCore — Current Project State

Current release: **V1.0-R5.7.41.3.4.10.8 — Viewing→Glow Molecular Context Handoff**

Science baseline remains frozen at `R5.7.41.2_SHADOW_COT_AB_FROZEN`.

## Runtime roadmap status

- `.10.1` Observer Aerosol Numeric Route Context：FIELD PASS
- `.10.2` Molecular Numeric Route Context：FIELD PASS
- `.10.3` Observer Precipitation Horizontal-Support Ray Reuse：FIELD PASS
- `.10.4` Gas Spectroscopy State Memo：FIELD PASS
- `.10.5` Route Group Direct Reuse：science exactness PASS / runtime NOT FIELD PASS
- `.10.6` Cloud Numeric Route Context：FIELD PASS
- `.10.7` Viewing↔Glow Shared Hydrometeor Context：**FIELD PASS**（TWS091 2026-09-14 sunrise，8.250749 → 2.407172 s）
- `.10.8` Viewing→Glow Molecular Context Handoff：REGRESSION PASS / FIELD TEST CANDIDATE

## `.10.8` purpose

Eliminate duplicate Glow molecular-route preparation by handing off the exact z/T/P arrays already prepared in Main Viewing gas contexts. Glow rebuilds only independent near-surface boundary metadata. Any incomplete/invalid shared context fails closed to the existing `.10.2` independent preparation path.

## Baseline for next Field run

2026-09-14 sunrise TWS091 `.10.7`:
- Glow Lookup Context Prep：6.647128 s
- Glow Volume Assembly：7.226424 s
- Glow Observer Spectral：3.087648 s
- Glow Observer Precipitation：2.407172 s
- Glow total：22.970400 s

Primary `.10.8` Field gate：`TWILIGHT_GLOW_COMPONENT_LOOKUP_CONTEXT_PREP` must materially decline; net Glow time must not regress.
