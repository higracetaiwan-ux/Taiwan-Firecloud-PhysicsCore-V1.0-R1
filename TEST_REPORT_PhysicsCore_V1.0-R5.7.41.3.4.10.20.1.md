# Test Report — PhysicsCore V1.0-R5.7.41.3.4.10.20.1

## QA Regression

Command:

```text
pytest -q
```

Result:

```text
846 passed, 1 warning
```

Warning is the existing pandas `FutureWarning` in `test_r5732_glow_observer_aerosol_coverage.py`; it is not a failure.

## Step 3C–3G Focused Regression

Result before release packaging:

```text
46 passed
```

## Step 3G Diagnostic Preflight

- Cases: 18
- Max IWC mass-closure relative error: ~`3.55e-16`
- Max 20 µm branch continuity relative error: ~`1.25e-15`
- Max normalization convergence relative error: ~`8.20e-7`
- Diagnostic numerical pass: YES
- Scientific mass-closure pass: NO (by contract)
- Production Ice Optics: NO

## FIELD Status

No new `.10.20.1` FIELD CASE has been executed inside this release-build session. Therefore this release is **QA PASS / FIELD validation pending**, not FIELD PASS.


## Extended Step 3G / CASE Integrity Regression

包含 Step 3C–3G、CASE evidence handoff 與 archive integrity：

```text
55 passed
```

## Release-build Metadata Regression

`.10.20.1` milestone 由 `Synthetic Closure Harness` 升為 `Diagnostic Mass-Closure Preflight` 後，UI information-architecture 測試曾保留舊 milestone 字串；已同步更新測試契約。針對該測試檔重跑：

```text
4 passed
```


## FULL-CLEAN Preflight Fresh-Extract Verification

Preflight package structure：

```text
1050 members
0 forbidden cache/bytecode members
```

將 preflight ZIP 解壓到全新目錄後執行：

```text
python -m pytest -q
846 passed, 1 warning
```

第一次把打包、解壓與 pytest 放在同一個 120 秒命令中時，命令在測試接近完成時逾時；沒有 pytest failure 記錄。之後對已解壓目錄單獨 fresh-run，完整 846/846 PASS。
