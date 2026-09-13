# Test Report — V1.0-R5.7.41.3.4.10.8

## Targeted regression

- `.10.8` molecular handoff + `.10.2` molecular context + Glow profiler adjacent chain：**12/12 PASS**。
- Shared Viewing context rebuild vs independent legacy molecular routes：exact distances / z / T / P / lower-boundary metadata。
- Invalid shared gas context：forces `.10.2` fallback。
- Complete shared context：legacy molecular preparation is not called.

## Actual-case structural exactness

2026-09-14 TWS091 sunrise `.10.7` CASE：

- gas profile rows：53,404
- exact routes：39
- distance profiles：2691
- field differences：0
- legacy prep median：3.537930 s
- shared handoff median：0.115728 s
- local speedup：約 30.57×

## Full working-tree regression

Complete collected suite：**687 tests**。Due to execution ceilings, mutually exclusive file groups were used.

- 160 PASS
- 114 PASS
- 67 PASS
- 36 PASS
- 53 PASS（1 existing pandas FutureWarning）
- 71 PASS
- 112 PASS
- 74 PASS
- Combined：**687/687 PASS**

## FULL-CLEAN fresh-extract gate

First FULL-CLEAN archive fresh-extract, mutually exclusive groups:

- 83 PASS
- 92 PASS
- 83 PASS
- 85 PASS
- 77 PASS
- 56 PASS
- 33 PASS
- 77 PASS（1 existing pandas FutureWarning）
- 101 PASS
- Combined：**687/687 PASS**

Archive hygiene：0 `__pycache__`, `.pytest_cache`, `.pyc/.pyo`, `.firecloud_state`, `.firecloud_cache`.

Final repack fresh-extract, mutually exclusive groups:

- 83 PASS
- 92 PASS
- 83 PASS
- 85 PASS
- 77 PASS
- 89 PASS
- 77 PASS（1 existing pandas FutureWarning）
- 101 PASS
- Combined：**687/687 PASS**
