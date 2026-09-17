# Test Report — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.24

狀態：**QA PASS；FULL-CLEAN fresh-extract PASS；FIELD VALIDATION PENDING**

## TDD / focused

- Step 3K core：5/5 PASS（先 RED：module missing，再 GREEN）。
- Step 3K model / Analysis Integrity / CASE handoff：3/3 PASS（先 RED，再 GREEN）。
- Step 3K + handoff + UI focused：12/12 PASS。

## Full regression（working tree）

- `882 passed, 1 warning in 55.67s`
- exit code 0。
- warning 為既有 pandas `FutureWarning`，非失敗。
- 測試容器預設 Datadog tracing 曾在 pytest summary 完成後留下 `TelemetryWriter` / `tokio-runtime-worker`，造成外層 process 不退出；設定 `DD_TRACE_ENABLED=false` 後同一套 882 tests 正常 exit 0。這是容器 instrumentation teardown，不是 PhysicsCore thread/process leak，production code 未因而修改。

## Reproducibility

- Step 3K evidence regeneration：byte-exact PASS（11 rows）。
- Step 3K gate regeneration：byte-exact PASS（1 row）。
- Step 3K contract regeneration：byte-exact PASS。

## Step 3K numeric result

- 18-case independent optical cross-check matrix：executed。
- Fu/projected-area numeric chain：all PASS。
- 最大 Fu unit-chain relative error：`1.22441956002415e-05`。
- Step 3J Yang/Bi diagnostic bulk vs Fu independent chain relative-difference range：`0.2621271071414941 .. 0.3121662072653651`。
- 此差異僅做 scientific characterization，不視為 like-for-like production validation。

## Science gates

- Fu96 independent optical cross-check：PASS / executed。
- projected-area numeric chain：PASS。
- Dge dual semantics separated：PASS。
- Step 3J vs Fu difference characterized：PASS。
- Scientific bulk validation：BLOCKED。
- habit / roughness：BLOCKED。
- production bulk / tau / physics promotion：BLOCKED。

## FULL-CLEAN package-level validation

- 正式 FULL-CLEAN ZIP fresh-extract full regression：`882 passed, 1 warning in 76.11s`，exit code 0。
- Step 3K evidence fresh regeneration：byte-exact PASS（11 rows）。
- Step 3K gate fresh regeneration：byte-exact PASS（1 row）。
- Step 3K contract fresh regeneration：byte-exact PASS。
- ZIP cache hygiene：0 `__pycache__` / `.pytest_cache` / `.firecloud_cache` / `.pyc` / `.pyo`。
- 此版本仍為 QA PASS / FIELD VALIDATION PENDING；不得因 package-level PASS 解鎖 production Ice Optics。
