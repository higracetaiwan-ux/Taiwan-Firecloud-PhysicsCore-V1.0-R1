# Test Report — V1.0-R5.7.41.3.4.10.9

## Targeted + adjacent regression

- `.10.9` spectroscopy-cache handoff and adjacent Viewing/Glow/Gas chain：**27/27 PASS**。
- Same spectroscopy state with/without cache：exact output。
- Pre-seeded Main Viewing cache serves Glow without `_sigma_fast()` recompute。
- Missing LUT signature：legacy `_sigma_fast()` fallback，cache remains untouched。

## Actual-case exactness benchmark

2026-09-14 TWS091 sunrise `.10.8` CASE：

- Glow volumes：1092
- Main Viewing pre-filled sigma cache：約 450 entries
- Glow completion cache：約 11,394 entries
- gas-species path differences：0/1092
- legacy：約 2.844 s
- shared cache handoff：約 1.073 s
- local speedup：約 2.65×

## Full working-tree regression

Complete collected suite：**691 tests**。

- Combined：**691/691 PASS**
- Warning：1 existing pandas FutureWarning only; no new warning/failure.

## Source / frozen audit

Relative to `.10.8` FULL-CLEAN：

- `firecloud/*.py` total：80
- byte-identical：78
- changed：`firecloud/twilight_glow.py`, `firecloud/__init__.py`
- new/removed Python modules：0

## FULL-CLEAN fresh-extract gate

First FULL-CLEAN archive fresh-extract, mutually exclusive groups:

- 87 PASS
- 87 PASS
- 87 PASS
- 86 PASS（1 existing pandas FutureWarning）
- 86 PASS
- 86 PASS
- 86 PASS
- 86 PASS
- Combined：**691/691 PASS**

Archive hygiene：0 `__pycache__`, `.pytest_cache`, `.pyc/.pyo`, `.firecloud_state`, `.firecloud_cache`.

Final repack fresh-extract：**691/691 PASS**（87+87+87+86+86+86+86+86；1 existing pandas FutureWarning only）。
