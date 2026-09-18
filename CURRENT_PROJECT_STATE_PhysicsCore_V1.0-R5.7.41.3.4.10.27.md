# Taiwan Firecloud PhysicsCore — CURRENT PROJECT STATE

## 現行版本
- Development release：`1.0.0-R5.7.41.3.4.10.27`
- 狀態：**QA CANDIDATE / FIELD VALIDATION PENDING**
- Latest formal FIELD baseline：`V1.0-R5.7.41.3.4.10.26 FIELD PASS`
- Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`

## 本版內容
`.10.27` 是 Ice Optics Phase 2 **Step 3N — Fu96/RRTMG Independent Bulk-band SSA + Asymmetry Qualification**。

本版把 Fu (1996) / RRTMG `ssaice3`、`asyice3` 固定為與 Yang/Bi LUT 分離的 independent bulk-band reference chain，並把 RRTMG visible broad bands 與 PhysicsCore 550/575/600/650/700/750 nm 六個單色波段的關係寫成「spectral containment only」。

## 已完成
- Fu96 primary provenance：PINNED。
- RRTMG Fu96 `ssaice3` / `asyice3` implementation provenance：PINNED。
- RRTMG band 25（約 441.5–625 nm）→ 550/575/600 nm containment mapping：固定。
- RRTMG band 24（約 625–778.2 nm）→ 650/700/750 nm containment mapping：固定。
- independent bulk-band SSA reference available=true。
- independent bulk-band asymmetry reference available=true。
- CASE evidence / gate / contract handoff 與 integrity audit 已接線。

## 仍 fail-close
- `INDEPENDENT_SSA_VALIDATION_PASS=false`
- `INDEPENDENT_ASYMMETRY_VALIDATION_PASS=false`
- `FULL_SIX_BAND_LIKE_FOR_LIKE_OPTICAL_VALIDATION_PASS=false`
- `TAU_ICE_PRODUCTION_ALLOWED=false`
- `PRODUCTION_ICE_OPTICS_READY=false`
- `physics_promotion_allowed=false`

RRTMG broad-band 值不得複製或插值後冒充六個 monochromatic truths。Step 3N 目前是 source/provenance + spectral-semantics qualification，不是 SSA/g numerical validation pass。

## QA
- Step 3N core / handoff / release identity：PASS。
- Step 3M + Step 3N + UI focused regression：19/19 PASS。
- Working-tree full regression：**910/910 PASS**，1 個既有 pandas `FutureWarning`。
- Candidate FULL-CLEAN：1179 members／0 cache-pyc artifacts／fresh-extract **910/910 PASS**（218 / 243 / 214 / 235）。
- Candidate Step 3N evidence / gate / contract：**byte-exact regeneration PASS**。
- Final immutable ZIP：本報告更新後重建，再執行最後 read-only verification。

## FIELD 下一步
只有 `.10.27` QA release closure 完成後，才使用 TWS091 sunrise 或等價 positive-IWP CASE 驗證 Step 3N artifacts deterministic handoff。FIELD PASS 只代表 Step 3N qualification/handoff 穩定，不代表 exact six-band SSA/g validation 或 Production Ice Optics 已解鎖。
