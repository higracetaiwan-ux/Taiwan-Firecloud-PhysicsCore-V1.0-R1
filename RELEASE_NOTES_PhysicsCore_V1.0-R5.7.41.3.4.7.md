# Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.7

## Viewing / Photography Runtime Hotspot Decomposition — Field-Test Candidate

本版延續 R5.7.41.3.4.6。`.3.4.6` warm Field CASE 已確認 `AGGREGATION_VIEWING_AND_PHOTOGRAPHY` 約 134.6 秒，是目前最大的非 Glow aggregation hotspot；但尚未證明其中哪個函式最慢，因此本版不猜測、不先改科學與解析度，而是先做 function-level profiler。

### 新增 profiler

新增九個 diagnostic-only performance stage：

- Viewing path geometry；
- Viewing precipitation evidence；
- Target optics / COT reconciliation attach；
- Viewing spectral runtime context preparation；
- Six-band viewing spectral extinction；
- Viewing spectral summary；
- Viewing spectral status attach；
- Viewing path summary；
- Photography decision。

所有 component rows 都標記 `R5741347_COMPONENT_PROFILE_ONLY`，只寫 telemetry，不參與科學判定。

### 保留 / 恢復 R5.7.41.3.4.6 runtime-I/O contract

- DWD persistent raw GRIB cache：exact model/product/grid/run/lead/variable/level/source URL identity；
- raw cache 命中前驗證 identity、byte size、SHA256、QC stamp；
- corruption / mismatch fail-close；
- atomic cache commit；
- DWD network attempts / successes / failures / bytes / cache-hit telemetry；
- CASE CSV 4 MiB bounded UTF-8 coalescing buffer；
- CASE pre-export / CSV / JSON / serialization profiler；
- aggregation stage decomposition。

### Frozen science SHA audit

與 R5.7.41.3.4.5 FULL-CLEAN 原始 archive 比較，下列 frozen science modules SHA256 **完全相同**：

`formation.py`, `viewing.py`, `viewing_spectral.py`, `twilight_glow.py`, `optical_path.py`, `target_canvas_optics.py`, `canvas_cot_semantic_migration.py`, `gas_rt.py`, `spectral_rt.py`, `spectral_color.py`, `illumination.py`, `photography_decision.py`, `canvas_vertical_microphysics_overlap.py`, `canvas_optical_vertical_conflict.py`。

因此本版目前變更面限於 orchestration profiler、runtime/I-O provider/cache、CASE streaming、版本與測試文件。

## Verification

- `.3.4.5` recovered baseline：619/619 PASS；
- R5.7.41.3.4.6 + .3.4.7 targeted tests：15/15 PASS；
- working-tree full regression：631/631 PASS；
- existing pandas FutureWarning：1（non-failure）。

Trial fresh-extract regression：631/631 PASS；FULL-CLEAN archive hygiene：0 cache/pyc。

## Field validation status

**PENDING**。

本版的目的就是取得 component-level timing；在 TWS106 warm Field CASE 回傳前，不宣稱已完成最大 hotspot 的最佳化，也不宣稱 `.3.4.7` FIELD PASS。
