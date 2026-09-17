# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.25.1

## 版本定位
`R5.7.41.3.4.10.25.1` 是 Ice Optics Phase 2 Step 3L.1：**Stable Contract Sample Serialization Hotfix**。

本版只修正 `.10.25` TWS091 FIELD CASE 暴露的 Step 3L contract 跨平台浮點尾數漂移；不進入 Step 3M，不修改 Frozen Science，也不改任何 production 決策規則。

## FIELD 根因
`.10.25 / TWS091 / 2026-09-18 sunrise` CASE：
- Step 3L evidence：12 rows，與 release byte-exact。
- Step 3L gate：1 row，與 release byte-exact。
- Step 3L contract：語意 gate 不變，但兩個 diagnostic sample 浮點字串出現平台差異：
  - `max_bulk_ssa_spread`
  - `max_grid_convergence_relative_error`
- CASE archive manifest 184 個 WRITTEN members 全部 SHA256 自洽，0 missing / 0 mismatch。
- 因 deterministic contract bytes 未成立，`.10.25` 不列 FIELD PASS；正式 FIELD baseline 仍為 `.10.24.1`。

## 修正
- 保留 `STABLE_EVIDENCE_SIGNIFICANT_DIGITS = 11`，不改現有 Step 3L evidence/source-row serialization。
- 新增 `STABLE_CONTRACT_SAMPLE_SIGNIFICANT_DIGITS = 8`。
- 新增 `_stable_contract_sample()`，只套用於 `sample_roughness_bulk_ensemble` 四個 diagnostic sample 欄位。
- 科學計算仍使用 full double precision；只有 persisted contract diagnostic sample 文字被 canonicalize。
- 新增 FIELD-observed variants regression test，確認兩組實際平台尾數可收斂到相同 contract sample payload。

## 不變項目
- Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`。
- Formation / Viewing / Twilight Glow 分離不變。
- 六波段 550/575/600/650/700/750 nm 不變。
- `exact_geometry_equivalence=false`。
- `gfs_native_habit_inference=false`。
- `runtime_habit_default_allowed=false`。
- `runtime_roughness_default_allowed=false`。
- `tau_ice_production_allowed=false`。
- `production_ice_optics_ready=false`。
- `physics_promotion_allowed=false`。

## QA
- 新增 tests 後 working-tree regression：**894/894 PASS**。
- 唯一 warning：既有 pandas `FutureWarning`，非本版新增。
- FIELD validation：**PENDING**；不得在 `.10.25.1` CASE 重跑前稱 FIELD PASS。
