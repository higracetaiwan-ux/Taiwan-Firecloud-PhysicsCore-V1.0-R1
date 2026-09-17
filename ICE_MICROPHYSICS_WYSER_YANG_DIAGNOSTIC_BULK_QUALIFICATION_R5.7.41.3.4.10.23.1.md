# Ice Microphysics — Step 3J.1 Hotfix Qualification

Version: `V1.0-R5.7.41.3.4.10.23.1`

Science Step: `R5.7.41.3.4.10.23 Step 3J`

Science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`

## Scope

本版不改 Step 3J 的 `β_ext` / `k_ext` 數值計算，只修正兩個 release/CASE 證據問題：

1. CAMS isolated child 回傳 `TIMEOUT_DEFERRED` 時，durable checkpoint 必須同步寫成 terminal `TIMEOUT_DEFERRED`，不得殘留 `STARTED/RUNNING`。
2. Step 3J evidence-only 浮點文字固定使用 **16 significant digits**，消除不同 runtime / platform 最後 1 ULP 的 byte drift。

## Reproduced FIELD defect

`.10.23 TWS100` 的 request audit 已記錄：

- role: `PRESSURE_LEVEL_CHEMISTRY_OPTICS_BUNDLE`
- final status: `TIMEOUT_DEFERRED`
- reason: `CAMS_ADS_QUEUE_GRACE_EXCEEDED`

但 `cams_worker_checkpoints.json` 同一 worker token 仍為 `RUNNING`。Root cause 是 `_run_cams_role_isolated()` 對 child result `TIMEOUT_DEFERRED` 明確跳過 terminal checkpoint write。

## Hotfix contract

- `TIMEOUT_DEFERRED` child envelope → durable checkpoint `TIMEOUT_DEFERRED`
- 保存 PID / exit code / elapsed / error / request/result/stdout/stderr paths
- parent wall-clock timeout 的既有 `O3_ADS_TIMEOUT` / `CAMS_ADS_TIMEOUT` contract 不變
- Failed / Missing / Incomplete terminal mapping 不變
- `stable_evidence_float()` 僅用於 evidence text serialization；不進入科學計算

## Frozen gates

仍維持：

- `SCIENTIFIC_BULK_VALIDATION_PASS=false`
- `YANG_BI_HABIT_BRIDGE_VALIDATED=false`
- `YANG_BI_ROUGHNESS_BRIDGE_VALIDATED=false`
- `BULK_YANG_BI_PSD_INTEGRATION_ELIGIBLE=false`
- `TAU_ICE_PRODUCTION_ALLOWED=false`
- `PRODUCTION_ICE_OPTICS_READY=false`
- `physics_promotion_allowed=false`

## QA

- hotfix RED→GREEN regression: PASS
- related focused regression: 83/83 PASS
- working-tree full regression: 874/874 PASS
- FIELD validation: pending; priority replay = TWS100 sunrise 2026-09-17
