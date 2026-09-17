# R5.7.41.3.4.10.24 FIELD Validation — TWS100 2026-09-17 sunrise

## 結論
`V1.0-R5.7.41.3.4.10.24` 為 **Step 3K FIELD SCIENCE PASS / Evidence Reproducibility Hotfix Required**。

## CASE integrity
- Analysis job / worker：COMPLETED，exit code 0，WARM_PRODUCTION。
- Analysis Integrity：130 PASS / 1 NOT_APPLICABLE / 0 FAIL。
- CASE Integrity：113/113 PASS。
- Manifest：181/181 artifacts present、181/181 size match、181/181 SHA256 match。

## Step 3K
- Evidence：11 rows。
- Gate：1 row。
- Contract：`FIRECLOUD_ICE_FU96_INDEPENDENT_BULK_VALIDATION_V1`。
- Fu96 cross-check executed / projected-area numeric / Dge semantics separation：PASS。
- Scientific bulk validation、habit、roughness、bulk production、`tau_ice`、physics promotion：保持 blocked/false。

## Runtime fail-close
52 個 positive-IWP rows 仍沒有 runtime Dmax / habit / roughness / k_ext / tau_ice；沒有 Formation promotion。

## Blocker
CASE 與 release 的 Step 3K evidence/contract 出現約 `1e-16` 等級 platform floating drift，例如：
- `1.22441956002415e-05` vs `1.224419560031046e-05`
- `0.26212710714149406` vs `0.262127107141494`
- `0.31216620726536515` vs `0.31216620726536526`

無科學差異，但違反 deterministic evidence reproduction 要求，因此進 `.10.24.1` hotfix。
