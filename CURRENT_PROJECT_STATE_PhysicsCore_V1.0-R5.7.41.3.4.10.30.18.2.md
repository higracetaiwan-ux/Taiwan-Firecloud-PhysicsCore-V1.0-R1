# Taiwan Firecloud PhysicsCore — Current Project State

## 現行版本
- Engineering version：`1.0.0-R5.7.41.3.4.10.30.18.2`
- Frozen science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`
- Step3Q provenance baseline：`R5.7.41.3.4.10.30.18 / V1_18`
- 最新正式 FIELD baseline：`R5.7.41.3.4.10.30.17 FIELD PASS`
- `.10.30.18`：TWS100 FIELD FAIL — CAMS aerosol deferred timeout。
- `.10.30.18.1`：TWS100 FIELD FAIL — hotfix 僅覆蓋 serial scheduler，production adaptive path 未 reattach。
- `.10.30.18.2`：QA PASS / FIELD pending。

## `.18.2` CAMS 修正
WARM_PRODUCTION 的 `WHOLE_ROUTE_FIRST_ADAPTIVE_SUBTILING` 現在與 serial scheduler 一樣，對 `TIMEOUT_DEFERRED` 執行 bounded same-request-ID reattach。queue (`accepted`) 與 running phase timeout 都可恢復；reattach-only 永遠禁止 fresh submit。

## Fail-close
journal / request ID 缺失、遠端 request 無法恢復、或 bounded reattach 仍未成功時，資料保持 Missing；不得補成 Clear、Zero 或 fabricated aerosol payload。Timeout 也不允許觸發 geographic subdivision 來重送多份 request。

## Step3Q
`.10.30.18` 的 Fu96 0.700 μm boundary、Band24 cross-boundary 與 non-unique inverse re-averaging barrier保持不變。Step 3R 仍 blocked。
