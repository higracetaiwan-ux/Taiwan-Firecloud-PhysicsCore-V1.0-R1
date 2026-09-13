# R5.7.41.3.4.10.7 — Viewing↔Glow Shared Hydrometeor Context

## 目的

消除 Main Viewing 與 Twilight Glow 對同一 `(time, solar_altitude_deg)` route snapshot 重複建立 native RWMR/SNMR/GRLE hydrometeor cells 的 runtime 成本。

## 實作

1. Main Viewing 在每個事件角度呼叫 `prepare_native_hydrometeor_context(route)` 一次。
2. 同一 prepared context 同時用於 Main Viewing precipitation evidence。
3. prepared context 以 `(str(time), float(solar_altitude_deg))` key 傳入 Twilight Glow。
4. Glow `_observer_precipitation()` 若 exact key 命中，直接把 prepared context 傳給 `build_viewing_precipitation_evidence()`；未命中則保留 legacy preparation fallback。

## Frozen science

不改：
- RWMR/SNMR/GRLE native fields
- pressure-level cell geometry
- 17-point curved-Earth Cloud→Observer LOS
- Q_EXT_VISIBLE=2
- rain/snow/graupel assumed radius/density
- horizontal-support grouping
- intersection order / tau accumulation order
- Missing ≠ Clear ≠ Zero
- Formation / Viewing / Twilight Glow separation

## Evidence

- Prepared vs direct Viewing precipitation output: `check_dtype=True, check_exact=True`.
- Glow supplied-context path tested to ensure no second native hydrometeor preparation occurs.
- Targeted/adjacent regression: 33/33 PASS.
- Full working-tree regression: 683/683 PASS (396 + 287, mutually exclusive test-file groups); one pre-existing pandas FutureWarning only.

## Field status

Release status: REGRESSION PASS / FIELD TEST CANDIDATE.
Primary field gate: `TWILIGHT_GLOW_COMPONENT_OBSERVER_PRECIPITATION` should materially decline from the 2026-09-14 TWS091 sunrise baseline of 8.250749 s while science outputs remain provider-consistent.
