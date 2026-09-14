# Test Report — V1.0-R5.7.41.3.4.10.9.3

## Working-tree regression

- Result: **703 passed**
- Failure: **0**
- Warning: 1 existing pandas `FutureWarning`

## 新增測試

`tests/test_r5741341093_observer_nearfield_cloud_environment.py`

涵蓋：

1. 版本識別。
2. coarse low cloud 非零但 native 3D 無雲柱時保留 mismatch。
3. native low-cloud geometry 存在時正確標記但不 promotion。
4. band summary 正確保留 coarse/native mismatch。
5. Analysis Integrity role separation PASS。
6. 若 diagnostic 嘗試 Formation promotion，Integrity 必須 FAIL。

## CASE archive contract

兩個新 diagnostic CSV 已加入 required archive members；舊 archive-contract tests 已同步更新。

## Frozen science source audit

Formation / Viewing / Viewing spectral / Twilight Glow / gas RT / COT / config / red-light / photography modules 相對 `.10.9.2` 均 byte-identical。

## Field status

目前：**REGRESSION PASS / FIELD RETEST CANDIDATE**。

正式 FIELD PASS 需新的 `.10.9.3` Field CASE。

## FULL-CLEAN / fresh-extract gate

- FULL-CLEAN ZIP entries: **784**
- cache/compiled contamination: **0**
- fresh-extract regression: **703/703 PASS**
- fresh-extract warning: same existing pandas `FutureWarning` only
