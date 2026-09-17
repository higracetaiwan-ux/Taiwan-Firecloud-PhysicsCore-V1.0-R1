# Taiwan Firecloud PhysicsCore — CURRENT PROJECT STATE

## 現行版本
- Development release：`1.0.0-R5.7.41.3.4.10.25`
- 狀態：**QA PASS / FIELD VALIDATION PENDING**
- Latest formal FIELD baseline：`V1.0-R5.7.41.3.4.10.24.1 FIELD PASS`
- Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`

## 本版內容
`.10.25` 是 Ice Optics Phase 2 Step 3L：Yang/Bi Habit + Roughness Qualification。

### 已解鎖
- Yang/Bi V2 source inventory：9 habits × 3 roughness × 189 Dmax × 6 bands，coverage complete。
- Wyser solid-column lineage → Yang/Bi `single_column` **model-family semantic bridge**：PASS。
- `Rough000/Rough003/Rough050` 三態 uncertainty ensemble：diagnostic executable。
- habit / roughness optical sensitivity 已量化。

### 仍維持 fail-close
- exact geometry equivalence：false。
- GFS native habit inference：false。
- runtime habit default：false。
- runtime roughness default：false。
- scientific production bulk qualification：false。
- `TAU_ICE_PRODUCTION_ALLOWED`：false。
- `PRODUCTION_ICE_OPTICS_READY`：false。
- `physics_promotion_allowed`：false。

## 前一 FIELD baseline
`.10.24.1 / TWS091 / 2026-09-18 sunrise` 已完成 FIELD audit：CASE archive/integrity PASS，Step 3K stable evidence reproducibility blocker 關閉；正式 baseline 已更新為 `.10.24.1 FIELD PASS`。

## QA
- Step 3L core / handoff / UI focused：PASS。
- Full working-tree regression：**892/892 PASS**，1 個既有 pandas FutureWarning。
- Candidate FULL-CLEAN fresh-extract：**892/892 PASS**；Step 3L artifacts byte-exact regeneration PASS。
- Final-verify FULL-CLEAN：**892/892 PASS**；Step 3L artifacts byte-exact regeneration PASS。
- Final package verification：**892/892 PASS**；Step 3L artifacts byte-exact regeneration PASS。
- 本報告更新後重建之 immutable ZIP：需再執行最後 read-only verification。

## FIELD 下一步
建議用 TWS091 與至少一個 positive-IWP CASE 驗證：Step 3L 12-row evidence + 1-row gate + contract 完整封存，且 runtime habit / roughness / `tau_ice` 仍維持 fail-close。
