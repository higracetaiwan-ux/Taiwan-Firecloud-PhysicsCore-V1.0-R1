# TEST REPORT — R5.7.41.3.4.10.14

## Targeted regression
Step 3 + prior Phase 2 + UI contract：`28 passed / 0 failed`。

## Full regression（working tree）
`790 passed / 0 failed / 1 warning`。

## Fresh-extract regression（第一次封裝）
- fresh-extract `firecloud.__version__`：`1.0.0-R5.7.41.3.4.10.14`
- `790 passed / 0 failed / 1 warning`
- elapsed：約 `28.57 s`

Warning：既有 pandas DataFrame concat `FutureWarning`，與 `.10.14` 無關。

## Archive cleanliness
- `__pycache__`：0
- `.pytest_cache`：0
- `.pyc/.pyo`：0

## Field status
尚未以 `.10.14` 產出新 FIELD CASE，因此目前標記：
**IMPLEMENTATION / REGRESSION PASS — FIELD VALIDATION PENDING**。

上一個正式 FIELD PASS：`.10.13`。
