# TEST REPORT — PhysicsCore V1.0-R5.7.41.3.4.10

## 結果
- Glow targeted regression: 39/39 PASS
- Working-tree full regression: 650/650 PASS
- Candidate FULL-CLEAN fresh-extract regression: 650/650 PASS
- Final FULL-CLEAN fresh-extract regression: 650/650 PASS
- Warning: 1 個既有 pandas FutureWarning，非失敗

## 新增 gates
1. `runtime_cache_stats["component_seconds"]` 含完整 7 個 internal Glow components。
2. profiler ON / OFF 的 Glow detail DataFrame `check_exact=True`。
3. profiler ON / OFF 的 Glow summary DataFrame `check_exact=True`。
4. `model.py` 明確輸出 10 個 `TWILIGHT_GLOW_COMPONENT_*` stage。
5. component rows 僅標記 `R57413410_COMPONENT_PROFILE_ONLY`，不寫回 science DataFrame。

## FULL-CLEAN hygiene
- 0 `__pycache__`
- 0 `.pytest_cache`
- 0 `.pyc` / `.pyo`
- 0 runtime `.cache` / `.firecloud_state`
- deployment required files present

## Release gate
CLOSED for local/fresh-extract packaging. Field profiler gate remains OPEN until a `.3.4.10` CASE measures the 10 Glow components.
