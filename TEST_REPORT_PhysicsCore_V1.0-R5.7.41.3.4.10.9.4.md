# Test Report — V1.0-R5.7.41.3.4.10.9.4

## Working-tree regression

- Result: **709 passed**
- Failure: **0**
- Warning: 1 existing pandas `FutureWarning`

## 新增測試

`tests/test_r5741341094_observer_environment_timeline.py`

涵蓋：

1. 版本識別。
2. T−60→T+30、5 分鐘 cadence。
3. coarse timeline 沿用既有 route linear interpolation。
4. native snapshot 只作 ±180 s nearest-existing handoff，不做時間插值。
5. +30 min 超過 −6° endpoint 後只標 `POST_MINUS6_DIAGNOSTIC_ONLY`。
6. summary + Analysis Integrity role separation。

## TWS106 actual-case offline validation

- point rows：855
- summary rows：171
- 4 個 timeline integrity checks：PASS
- 17:07→18:29 Ground Truth timestamps 均能對到 5-min timeline，最近差 28–147 秒。

## Frozen source audit

Formation / Viewing / Viewing spectral / Twilight Glow / Gas RT / COT / config / Red-Light / Photography Decision 相對 `.10.9.3` byte-identical。

## Field status

**REGRESSION PASS / FIELD RETEST CANDIDATE**。

## FULL-CLEAN / fresh-extract gate

- FULL-CLEAN ZIP entries: **796**
- cache/compiled contamination: **0**
- fresh-extract regression: **709/709 PASS**
- fresh-extract warning: same existing pandas `FutureWarning` only
