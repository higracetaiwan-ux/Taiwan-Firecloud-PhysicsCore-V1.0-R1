# Taiwan Firecloud PhysicsCore V1.0 — R5.7.41.3.4.10.30.18.2 Release Notes

## 版本定位
本版為 `.10.30.18.1` 的 CAMS production scheduler hotfix。Frozen science baseline 維持 `R5.7.41.2_SHADOW_COT_AB_FROZEN`；Step 3Q provenance 仍為 `.10.30.18 / V1_18`，不進 Step 3R。

## `.10.30.18.1` FIELD 發現
TWS100 / 2026-09-20 sunrise 實跑證明 `.18.1` 尚未覆蓋真正的 WARM_PRODUCTION scheduler。四條 aerosol role 在 ADS `accepted` queue 階段超過 `queue_grace=75 s`，形成 `CAMS_ADS_QUEUE_GRACE_EXCEEDED → TIMEOUT_DEFERRED`。實際 production path 為 `WHOLE_ROUTE_FIRST_ADAPTIVE_SUBTILING`，其 `_fetch_cams_role_adaptive()` 原本對 `TIMEOUT_DEFERRED` 直接 return，因此 `.18.1` serial scheduler 的 reattach 邏輯沒有被執行。

## `.18.2` 修正
新增 `R5.7.41.3.4.10.30.18.2_ADAPTIVE_QUEUE_RUNNING_SAME_REQUEST_ID_REATTACH_V1`：
- adaptive production path 對 queue-grace 與 running-grace 的 `TIMEOUT_DEFERRED` 都執行 bounded reattach；
- 只允許 durable `ads_request_id` + recovery-eligible request；
- recovery 必須 `reattach_only=True`，禁止 fresh submit；
- 保留 initial request ID、remote status、timeout reason 與 reattach telemetry；
- bounded reattach 仍失敗時保持 Missing；
- timeout 不觸發 adaptive geographic subdivision，避免複製遠端 ADS jobs。

Serial scheduler 的 `.18.1` same-request-ID reattach 同步升為 V2，但行為邊界不變。

## 科學與 provenance 不變
- Step3Q：`R5.7.41.3.4.10.30.18`
- Contract：`FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_18`
- evidence / gate：與 `.10.30.18` byte-exact identical。
- contract JSON：僅 `physicscore_version` 更新為 `.10.30.18.2`。
- Fu96 Band24 inverse re-averaging barrier、Production Ice Optics、Step 3R 全部維持 fail-close。

## QA
- CAMS targeted regression：72/72 PASS。
- Step3Q lineage：63/63 PASS。
- Full regression：990/990 PASS，0 failure。
- 唯一 warning：既有 pandas FutureWarning。
