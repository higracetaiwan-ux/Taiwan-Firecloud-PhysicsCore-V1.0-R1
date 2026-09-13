# R5.7.41.3.4.10.6 — Viewing / Glow Cloud Numeric Route Context Spec

## 目標

移除 `build_viewing_spectral_extinction()` 對相同 time/solar-angle/direction cloud route 的重複 pandas copy/filter/iterrows 成本，保持 Cloud→Observer 科學結果 exact-equivalent。

## Frozen science contract

本版不得修改：

- 25-point Cloud→Observer curved-Earth LOS
- `_projected_support_interval()` 的垂直連續性 / midpoint support 規則
- COT evidence selection 與 Production COT semantics
- cloud fraction occupancy expectation：`(1-CF)+CF*exp(-tau)`
- slant COT path-length scaling
- blocker / unresolved / direct-conflict 判定
- `Missing ≠ Clear ≠ Zero`
- cloud row 原始 route order 與 floating-point τ 累加順序
- Formation / Viewing / Twilight Glow branch separation

## Runtime implementation

1. Shared Viewing runtime context 保留原 `cloud_groups`。
2. 依實際 photographic targets，為每個 exact route 建立一次 numeric cloud records。
3. projected support 仍呼叫 frozen `_projected_support_interval()`，只將結果寫入既有 route support cache。
4. numeric record 保存原 row order所需值：distance/base/top/CF/layer/time/angle/consistency/support interval。
5. `_cloud_expected_tau_prepared()` 逐 record 使用相同 25-point LOS、同一 COT/truth maps、同一 diagnostics 與同一 τ/occupancy 累加順序。
6. exact route 無 prepared cloud context 時回到 legacy `_cloud_expected_tau()`，保留 empty/headerless fail-close 與既有 test/injection contract。

## Exactness gates

專屬 regression 必須涵蓋：

- resolved occupancy
- missing COT
- missing cloud fraction
- direct conflict
- geometric path clear
- headerless empty cloud evidence
- runtime-context reuse telemetry

Actual TWS134 same-input A/B：

- Main Viewing：585 targets，`check_dtype=True, check_exact=True`
- Twilight Glow observer spectral：1092 targets，`check_dtype=True, check_exact=True`
- CSV SHA256 exact match
