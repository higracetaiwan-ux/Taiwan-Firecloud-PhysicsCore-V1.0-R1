# Taiwan Firecloud PhysicsCore — Current Project State

## 現行版本
- Engineering version：`1.0.0-R5.7.41.3.4.10.30.18.1`
- Frozen science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`
- Step3Q provenance baseline：`R5.7.41.3.4.10.30.18 / V1_18`
- 最新正式 FIELD baseline：`R5.7.41.3.4.10.30.17 FIELD PASS`
- `.10.30.18`：TWS100 FIELD FAIL，根因為 CAMS aerosol spectral payload deferred timeout。
- `.10.30.18.1`：QA PASS / FIELD pending。

## 本版 CAMS 修正
`TIMEOUT_DEFERRED` 不再只 cooldown 後永久跳過同一 role。當 durable request ID 存在時，scheduler 在同一分析 run 中進行 bounded same-request-ID reattach。reattach-only 模式禁止 fresh submit，因此不會以修 timeout 為代價製造 duplicate ADS jobs。

## Fail-close
若 reattach journal/request ID 不存在、遠端 request 無法恢復、或 bounded reattach 仍未完成，資料維持 Missing，analysis integrity 仍可 FAIL。不得以 cache guess、zero、clear 或 fabricated aerosol payload 代替。

## Step3Q 狀態
`.10.30.18` 的 Fu96 0.700 μm boundary / Band24 non-unique inverse re-averaging barrier 全部不變。Step 3R 仍 blocked。
