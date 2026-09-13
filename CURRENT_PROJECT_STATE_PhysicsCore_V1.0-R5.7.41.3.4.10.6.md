# Taiwan Firecloud PhysicsCore — Current Project State

## Current release

**V1.0-R5.7.41.3.4.10.6 — Viewing / Glow Cloud Numeric Route Context**

Science baseline remains frozen at **R5.7.41.2_SHADOW_COT_AB_FROZEN**.

## Latest Field result — `.10.5` TWS134

- Analysis Integrity：72/72 PASS
- CASE Integrity：32/32 PASS
- 67/67 `v1_*.csv` byte-for-byte identical vs `.10.4`
- CAMS/GFS/DWD forecast cycles are the same between `.10.4` and `.10.5`
- Observer Spectral Extinction：6.642 → 7.085 s（+6.7%）
- Glow total：23.364 → 32.202 s
- `.10.5 = science exactness PASS / runtime NOT FIELD PASS`

## `.10.6` implementation

Actual-case profiling identified `_cloud_expected_tau()` pandas cloud-row materialization as the next concentrated non-provider cost.

`.10.6` adds exact-order cloud numeric route context:

- same route rows and order
- same projected-support geometry
- same 25-point Cloud→Observer LOS
- same COT/CF and occupancy expectation
- same conflict/Missing diagnostics
- same τ accumulation order
- legacy fallback when no exact prepared cloud context exists

Actual TWS134 same-input A/B:

- Main Viewing 585 targets exact
- Glow 1092 targets exact

Working-tree full regression：678/678 PASS.

Final FULL-CLEAN fresh-extract regression：678/678 PASS；release gate CLOSED.

## Next Field gate

Deploy `.10.6` and rerun **TWS134 / 2026-09-13 sunset**.

Primary gate：`TWILIGHT_GLOW_COMPONENT_OBSERVER_SPECTRAL_EXTINCTION` should fall clearly below `.10.5` 7.085 s / `.10.4` 6.642 s without science-output drift.
