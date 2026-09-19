# Taiwan Firecloud PhysicsCore V1.0 — R5.7.41.3.4.10.30.18.1 Release Notes

## 版本定位
本版為 `.10.30.18` 的 CAMS runtime reliability hotfix。Frozen science baseline 維持 `R5.7.41.2_SHADOW_COT_AB_FROZEN`，Step 3Q provenance 維持 V1_18，不進 Step 3R。

## FIELD 問題來源
TWS100 / 2026-09-20 sunrise 的 `.10.30.18` FIELD CASE 中，四條 CAMS aerosol request 在 ADS 已進入 `running` 後超過本地 running grace，回傳 `TIMEOUT_DEFERRED`。遠端 request ID 雖已持久化且遠端 job 仍可能繼續執行，但 serial scheduler 在同一次分析中不再回到該 role 收割完成結果，造成 spectral aerosol payload 全 Missing，觸發 `CAMS_AEROSOL_SPECTRAL_PAYLOAD_VALIDITY=FAIL`。

## 修正
新增 `R5.7.41.3.4.10.30.18.1_SAME_REQUEST_ID_BOUNDED_REATTACH_V1`：
- `TIMEOUT_DEFERRED` 且 audit 證明具有 durable `ads_request_id` / recovery eligibility 時，同一次分析允許有限次 reattach recovery。
- recovery child 使用 `reattach_only=True`。
- reattach-only 模式只能 `get_remote(request_id)`，禁止 fresh `submit()`；journal 缺失、request ID 缺失或遠端不可恢復時直接 fail-close。
- 預設 `FIRECLOUD_CAMS_DEFERRED_REATTACH_COUNT=1`。
- 預設 `FIRECLOUD_CAMS_DEFERRED_REATTACH_COOLDOWN_SECONDS=8`。
- reattach 仍未成功則維持 `TIMEOUT_DEFERRED` / Missing，不補值、不轉 Clear/Zero。
- request audit 新增 deferred reattach telemetry。

## 科學與 provenance 不變
- Step3Q version：`R5.7.41.3.4.10.30.18`
- Contract：`FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_18`
- evidence CSV：與 `.10.30.18` byte-exact identical。
- gate CSV：與 `.10.30.18` byte-exact identical。
- contract JSON：除 `physicscore_version` 更新為 `.10.30.18.1` 外，其餘內容相同。
- Production Ice Optics、exact Band24/25 reproduction、Step 3R 全部保持 fail-close。

## QA
- CAMS targeted regression：28/28 PASS。
- Step3Q lineage：60/60 PASS。
- Full regression：987/987 PASS，0 failure。
- 唯一 warning 為既有 pandas FutureWarning。
