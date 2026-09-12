# Test Report — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.7

## Scope

Runtime/I-O + Viewing/Photography profiler candidate. Science baseline remains `R5.7.41.2_SHADOW_COT_AB_FROZEN`.

## Results

- Recovered `.3.4.5` baseline before changes: **619/619 PASS**.
- New `.3.4.6` runtime/I-O + `.3.4.7` profiler targeted/compatibility suite: **15/15 PASS**.
- Working-tree full regression: **631/631 PASS**.
- Trial FULL-CLEAN fresh-extract full regression: **631/631 PASS**.
- Existing pandas FutureWarning: **1**, non-failure.
- Trial archive hygiene: **0** `__pycache__`, `.pytest_cache`, `.pyc`, `.firecloud_state`, `.firecloud_cache` members.

## Frozen-science SHA audit

Exact SHA256 equality against `.3.4.5 FULL-CLEAN` confirmed for:

- `formation.py`
- `viewing.py`
- `viewing_spectral.py`
- `twilight_glow.py`
- `optical_path.py`
- `target_canvas_optics.py`
- `canvas_cot_semantic_migration.py`
- `gas_rt.py`
- `spectral_rt.py`
- `spectral_color.py`
- `illumination.py`
- `photography_decision.py`
- `canvas_vertical_microphysics_overlap.py`
- `canvas_optical_vertical_conflict.py`

## Field validation

**PENDING**. Use 2026-09-12 Sunset / TWS106 高美濕地 warm-provider-cache CASE. The purpose is to identify the largest of the nine new component timers before any second-phase optimization.
