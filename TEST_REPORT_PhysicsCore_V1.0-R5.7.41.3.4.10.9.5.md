# Test Report — V1.0-R5.7.41.3.4.10.9.5

## Working-tree regression

- Result: **715 passed**
- Failure: **0**
- Warning: 1 existing pandas `FutureWarning`

## 新增測試

`tests/test_r5741341095_gfs_hourly_valid_time_alignment.py`

涵蓋：

1. TWS106 10:00:21 UTC → 06Z f004，不再 f003。
2. TWS106 −6° 10:26:48 UTC → 最近 hourly f004。
3. f000–f120 hourly / f123–f384 3-hourly cadence。
4. `pgrb2` / `pgrb2b` request filename 使用相同 f004。
5. `GFS_NATIVE_VALID_TIME_ALIGNMENT` provenance gate PASS。
6. 不一致 offset 會被 Integrity gate FAIL。

既有 provider-cycle-freeze 測試同步更新，但 frozen analysis clock / cycle availability contract 不變。

## Frozen science audit

本版功能變更限定於：

- `firecloud/providers/gfs_native.py`
- `firecloud/providers/gfs_canvas_optical_probe.py`
- `firecloud/model.py`（audit provenance handoff）
- `firecloud/case_integrity.py`（valid-time integrity）
- version/tests/docs

Formation / Viewing / Twilight Glow / Gas RT / COT / Red-Light / Photography Decision science implementation未修改。

## Field status

**REGRESSION PASS / FIELD RETEST CANDIDATE**。

## FULL-CLEAN / fresh-extract gate

- clean source files: **805**
- cache/compiled contamination before packaging: **0**
- fresh-extract regression: **715/715 PASS**
- fresh-extract warning: same existing pandas `FutureWarning` only

- FULL-CLEAN ZIP entries: **819**
