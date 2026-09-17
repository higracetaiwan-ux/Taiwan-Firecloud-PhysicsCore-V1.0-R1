# Taiwan Firecloud PhysicsCore — CURRENT PROJECT STATE

## 現行版本
- Development release：`1.0.0-R5.7.41.3.4.10.24.1`
- 狀態：**QA PASS / FIELD VALIDATION PENDING**
- Latest formal FIELD baseline：`V1.0-R5.7.41.3.4.10.23.1 FIELD PASS`
- `.10.24`：Step 3K FIELD SCIENCE PASS / stable evidence serialization hotfix required
- Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`

## 本版內容
`.10.24.1` 不改 Step 3K 科學計算，只將 Step 3K evidence / contract 的 floating output canonicalize 為 11 significant digits，以消除 CASE/release 約 `1e-16` 等級跨平台 byte drift。

## Step 3K science status
- Fu96 independent optical cross-check：executed / numeric PASS。
- 18-case difference characterization：保留 `.10.24` 結果，約 26–31%。
- Scientific bulk validation：false。
- Yang/Bi habit bridge：false。
- Yang/Bi roughness bridge：false。
- Bulk production eligibility：false。
- `TAU_ICE_PRODUCTION_ALLOWED`：false。
- `PRODUCTION_ICE_OPTICS_READY`：false。
- `physics_promotion_allowed`：false。

## FIELD 下一步
只需重跑 TWS100 / 2026-09-17 sunrise，確認 Step 3K evidence/gate/contract 與 release static artifacts deterministic exact match，且 positive-IWP runtime 持續 fail-close。
