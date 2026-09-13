# Test Report — V1.0-R5.7.41.3.4.10.3

## Targeted
`test_r574134103_viewing_precip_horizontal_support_ray_reuse.py`: **6/6 PASS**。

涵蓋：
- grouped vs legacy exact equality
- one 17-point LOS per horizontal support
- science DataFrame values match legacy
- Missing intersecting layer semantics
- resolved-zero no-intersection semantics
- version contract

## Broader targeted
`.10/.10.1/.10.2/.10.3` related targeted suite：PASS。

## Full working-tree regression
**665/665 PASS**，1 個既有 pandas FutureWarning。

## Synthetic isolated integrator benchmark
300 iterations：legacy / grouped 約 **2.46×** speedup；只作結構性 benchmark，不視為 Field speedup。

## Final package gate
FULL-CLEAN fresh-extract：**665/665 PASS**，1 個既有 pandas FutureWarning。

Archive hygiene：0 `__pycache__`、0 `.pytest_cache`、0 `.pyc/.pyo`、0 `.firecloud_state/.firecloud_cache`。
