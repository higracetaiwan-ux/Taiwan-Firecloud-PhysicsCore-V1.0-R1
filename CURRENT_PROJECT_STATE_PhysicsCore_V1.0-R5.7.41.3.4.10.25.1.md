# Taiwan Firecloud PhysicsCore — CURRENT PROJECT STATE

## 現行版本
- Development release：`1.0.0-R5.7.41.3.4.10.25.1`
- 狀態：**QA PASS / FIELD VALIDATION PENDING**
- Latest formal FIELD baseline：`V1.0-R5.7.41.3.4.10.24.1 FIELD PASS`
- Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`

## 本版內容
`.10.25.1` 是 Ice Optics Phase 2 Step 3L.1 Stable Contract Sample Serialization Hotfix。

`.10.25` TWS091 FIELD candidate 的 archive/integrity 與 Step 3L evidence/gate 均 PASS，但 contract 的兩個 diagnostic sample 浮點字串在不同執行環境出現尾數漂移，因此 `.10.25` 維持 **QA PASS / FIELD BLOCKED BY REPRODUCIBILITY**，不得列 FIELD PASS。

### 本版修正
- Step 3L evidence/source-row serialization：維持 11 significant digits。
- Step 3L contract `sample_roughness_bulk_ensemble`：改用專用 8 significant digits canonicalization。
- full-double scientific calculations 不變。
- FIELD-observed platform variants regression 已加入。

### 仍維持 fail-close
- exact geometry equivalence：false。
- GFS native habit inference：false。
- runtime habit default：false。
- runtime roughness default：false。
- scientific production bulk qualification：false。
- `TAU_ICE_PRODUCTION_ALLOWED`：false。
- `PRODUCTION_ICE_OPTICS_READY`：false。
- `physics_promotion_allowed`：false。

## QA
- Working-tree regression：**894/894 PASS**，1 個既有 pandas FutureWarning。
- Candidate FULL-CLEAN：1151 members／fresh-extract **894/894 PASS**。
- Candidate Step 3L evidence / gate / contract：byte-exact regeneration PASS。
- Final immutable ZIP：待本報告更新後重建並執行最後 read-only verification。

## FIELD 下一步
重跑 `.10.25.1 / TWS091 / 2026-09-18 sunrise` 或等價 positive-IWP CASE，必須同時確認：
1. Step 3L evidence 12 rows、gate 1 row、contract 完整封存；
2. CASE 與 release Step 3L 三件 artifacts deterministic reproduction；
3. positive-IWP rows 仍保持 `ice_habit=UNKNOWN`、`surface_roughness=UNKNOWN`、`tau_synthesis_allowed=false`、`formation_promotion_allowed=false`；
4. 不進 Step 3M，直到 `.10.25.1` FIELD closure 完成。
