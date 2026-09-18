# Taiwan Firecloud PhysicsCore V1.0 — R5.7.41.3.4.10.30.1.1 Release Notes

## 類型

FIELD integrity hotfix；**不變更任何 Science baseline、Step 3Q.1 科學證據、權重語義或 production gate**。

## 修正內容

TWS106 / 2026-09-18 sunset FIELD CASE 顯示 Step 3Q.1 evidence、gate、contract 皆正確，且 CASE↔release byte-exact，但 `firecloud/case_integrity.py` 仍比對 Step 3Q 舊 fail-close state：

`PASS_FAIL_CLOSED_EXACT_WEIGHTING_PROVENANCE_UNRESOLVED`

Step 3Q.1 現行合法 state 為：

`PASS_FAIL_CLOSED_WEIGHTING_SEMANTIC_CLASS_QUALIFIED_EXACT_HISTORY_UNRESOLVED`

本版只更新 integrity matcher，並新增真實 evidence/gate/contract 的 regression test。

## 凍結不變

- Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`
- Formation / Viewing / Twilight Glow
- 六波段 550/575/600/650/700/750 nm
- Step 3Q.1 semantic qualification
- `EXACT_FU96_BAND_WEIGHTING_AVAILABLE = false`
- `TAU_ICE_PRODUCTION_ALLOWED = false`
- `PRODUCTION_ICE_OPTICS_READY = false`
- Missing ≠ Zero ≠ Clear

## 驗證

- Full regression：937/937 PASS
- Step 3Q.1 hotfix targeted regression：PASS
- TWS106 原 CASE manifest：199/199 SHA256 PASS
- 原 CASE Step 3Q.1 evidence/gate/contract：CASE↔release byte-exact

本版需要新的 FIELD CASE，才能正式升為 FIELD PASS。
