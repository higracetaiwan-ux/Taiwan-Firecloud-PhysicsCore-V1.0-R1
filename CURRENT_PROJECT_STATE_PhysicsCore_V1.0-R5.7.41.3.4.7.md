# Taiwan Firecloud PhysicsCore — Current Project State

Current development candidate: **V1.0-R5.7.41.3.4.7**.

Last field-closed release: **V1.0-R5.7.41.3.4.6**.

Science baseline remains frozen:

`R5.7.41.2_SHADOW_COT_AB_FROZEN`

## Why R5.7.41.3.4.7 exists

R5.7.41.3.4.6 TWS106 warm Field CASE showed:

- `AGGREGATION_VIEWING_AND_PHOTOGRAPHY ≈ 134.612 s`；
- this is ~78% of non-Glow aggregation；
- `build_viewing_spectral_extinction()` is only a hypothesis, not proven。

Therefore `.3.4.7` first adds component-level profiler and does **not** pre-optimize an unproven suspect.

## Field-test target

Re-run:

**2026-09-12 Sunset｜TWS106 高美濕地**

Prefer warm provider caches. Return the generated CASE ZIP. The next decision will be based on these nine rows in `performance_diagnostics.csv`:

- `VIEWING_COMPONENT_PATH_GEOMETRY`
- `VIEWING_COMPONENT_PRECIPITATION_EVIDENCE`
- `VIEWING_COMPONENT_TARGET_OPTICS_RECONCILIATION`
- `VIEWING_COMPONENT_PREPARE_SPECTRAL_RUNTIME_CONTEXT`
- `VIEWING_COMPONENT_SPECTRAL_EXTINCTION`
- `VIEWING_COMPONENT_SPECTRAL_SUMMARY`
- `VIEWING_COMPONENT_ATTACH_SPECTRAL_STATUS`
- `VIEWING_COMPONENT_PATH_SUMMARY`
- `VIEWING_COMPONENT_PHOTOGRAPHY_DECISION`

## After Field CASE

Only optimize the measured largest component. Allowed methods:

- remove repeated DataFrame filters/groupby；
- reuse exact same time-angle-direction route maps/indexes；
- reuse immutable gas/aerosol/cloud support context under strict identity；
- vectorize safe per-target loops；
- preserve legacy fallback on cache miss。

Forbidden:

- changing science weights/thresholds；
- reducing six-band or spatial resolution；
- Missing→0 / Missing→Clear；
- changing Formation/Viewing/Glow semantics；
- relaxing Shadow eligibility。

## Verification state

Working tree regression: **631/631 PASS**; one existing pandas FutureWarning only.
Trial fresh-extract: 631/631 PASS; archive hygiene: 0 cache/pyc.
