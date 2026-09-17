# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.24.1

## Step 3K Stable Evidence Serialization Hotfix

本版只修復 `.10.24` Step 3K evidence reproducibility。FIELD CASE 顯示 Fu96 diagnostic values 在不同 runtime/platform 可產生約 `1e-16` 等級差異，雖不具科學意義，但會破壞 CASE ↔ release byte-exact reproduction。

### Changes
- Step 3K evidence/output canonicalization：11 significant digits。
- Contract diagnostic numeric fields 使用同一 canonicalization 後保存為 JSON number。
- 新增 regression test，直接重現 TWS100 CASE 與 release 的 observed floating variants。
- UI release history 加入 `.10.24.1`。

### Frozen / fail-close
- Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`。
- Step 3K science version：`.10.24`。
- 不更動 Step 3J/3K equations or numeric integration。
- 不解鎖 scientific bulk validation、habit、roughness、production k_ext、`tau_ice` 或 Formation promotion。
