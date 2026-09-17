# CAMS Terminal Checkpoint Reconciliation + Stable Diagnostic Evidence Serialization

Version: `V1.0-R5.7.41.3.4.10.23.1`

## Problem

`.10.23 TWS100` 暴露 archive telemetry contradiction：request audit 已 `TIMEOUT_DEFERRED`，但 durable CAMS checkpoint 仍可能停在 `RUNNING`。另外 Step 3J evidence 的 `:.17g` 會保存 platform-specific 1-ULP 差異。

## Root cause

`_run_cams_role_isolated()` 在讀到 child result envelope 後，只有 `OK/CACHE_HIT` 寫 `COMPLETED`，`FAILED/INCOMPLETE/MISSING` 寫 `FAILED`，而 `TIMEOUT_DEFERRED` 被刻意排除，導致最後 heartbeat 沒有 terminal reconciliation。

## Fix

- child `TIMEOUT_DEFERRED` → `_write_cams_worker_checkpoint(..., status="TIMEOUT_DEFERRED")`
- 保留 worker exit code 與原始 error
- Step 3J evidence 使用 `stable_evidence_float(value)` = 16 significant digits
- 不修改 raw float、integration grid、PSD、Cext、β_ext、k_ext、τ、Formation/Viewing/Glow

## Acceptance

1. 模擬 child `TIMEOUT_DEFERRED` 的 durable checkpoint 必須為 terminal `TIMEOUT_DEFERRED`。
2. `35.736078690506133` 與 `35.736078690506126` 必須序列化為同一 evidence string `35.73607869050613`。
3. 全套 regression PASS。
4. TWS100 FIELD replay 的 checkpoint 不再殘留 `RUNNING`。
