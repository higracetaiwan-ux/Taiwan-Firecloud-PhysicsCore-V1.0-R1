# Viewing→Glow Observer-Cloud Provenance Handoff + Shared Runtime Context Spec — R5.7.41.3.4.5

## 1. Scope

本規格只處理 Runtime 重複計算；Science baseline 固定為：

`R5.7.41.2_SHADOW_COT_AB_FROZEN`

不得修改 Production / Shadow COT、Shadow eligibility、Earth Shadow、Formation、Viewing、Twilight Glow、六波段或 Missing 語義。

## 2. 問題

Twilight Glow 需要知道 Cloud→Observer path 若為 `VIEW_CLOUD_OPTICS_PARTIAL`，是否源自需保留的 cloud direct-evidence conflict。舊流程在 Viewing 已完成 blocker geometry 後，Glow 又逐 atmospheric volume 重新追一次相同 cloud blockers，只為重建 conflict provenance。

同一分析還會在 Viewing 與 Glow 重複建立：

- aerosol route groups；
- gas route groups；
- cloud route groups；
- prepared HITRAN gas contexts；
- exact COT lookup；
- target optical-truth lookup；
- projected cloud-support geometry。

## 3. R5.7.41.3.4.5 contract

### 3.1 Same-pass provenance handoff

`viewing_spectral._cloud_expected_tau()` 在原本的 blocker traversal 中，透過 optional diagnostic sink 同步保留：

- `state`
- `blocker_count`
- `unresolved_blocker_count`
- `conflict_blocker_count`
- `unresolved_layer_ids`
- `conflict_states`

既有 5-value return signature 不變，避免破壞舊 caller/test contract。

`build_viewing_spectral_extinction()` 將上述 provenance 寫入：

- `view_cloud_provenance_state`
- `view_cloud_unresolved_blocker_count`
- `view_cloud_conflict_blocker_count`
- `view_cloud_unresolved_layer_ids`
- `view_cloud_conflict_states`

Glow 優先消費這些 handoff 欄位；只有 legacy/external input 缺欄位時才執行 R5.7.41.3.4.4 retrace fallback。

### 3.2 Shared runtime context

`prepare_viewing_spectral_runtime_context()` 建立 process-local runtime context，供 Viewing 與 Glow 共用：

- grouped aerosol/gas/cloud route tables；
- prepared gas contexts；
- exact COT map；
- target optical-truth map；
- projected-support cache。

### 3.3 Identity safety guard

Runtime context 只在 source DataFrame 為建立 context 時的**同一個 in-memory object**才允許 reuse。

若任一 cloud / target optics / aerosol / gas source object identity 改變，必須重建 context，不允許依內容相似、shape 相同或 hash 猜測 reuse。

這避免：

- stale cache；
- 跨 CASE 汙染；
- 不同 run/lead 誤共用；
- Missing / conflict provenance 被舊資料覆寫。

## 4. Conflict semantics must remain exact

Handoff conflict 判定沿用 legacy Glow retrace 規則，包括：

- `DIRECT_EVIDENCE_CONFLICT`；
- `MULTISOURCE_DISAGREEMENT`；
- `UNRESOLVED_CONFLICT`；
- `CF_CLOUD_CONDENSATE_ZERO`；
- `CONDENSATE_CLOUD_CF_LOW`；
- resolver state 內含 `CONFLICT`。

`Missing != Clear != Zero` 不得因 cache/handoff 改變。

## 5. Fallback compatibility

若 observer spectral row 沒有 `view_cloud_provenance_state`，Glow 必須保留原本 `_observer_cloud_conflict_provenance()` fallback，以支援：

- 舊 CASE replay；
- external caller；
- unit test fixtures；
- 尚未產生新欄位的資料。

Fallback lookup/cache 採 lazy initialization，只有實際 fallback 時才建立。

## 6. Telemetry

Runtime telemetry 至少保留：

- `cloud_handoff_hit_count`
- `cloud_provenance_call_count`（fallback 次數）
- `viewing_runtime_context_reused`
- `shared_gas_context_source`
- projected-support cache entries

Model stage cache status：

`R5741345_VIEWING_GLOW_PROVENANCE_HANDOFF_SHARED_RUNTIME`

## 7. Verification

### Unit / regression

新增三項 regression：

1. Viewing same-pass diagnostic sink 與 legacy Glow retrace exact semantic equality。
2. Shared runtime context 僅對 exact same source objects reuse；`.copy()` 必須 rebuild。
3. Glow 有 Viewing handoff 時不得呼叫 legacy fallback retrace。

### Offline H004 equivalence benchmark

使用 2026-09-04 TWS021 保存資料、單一 −2°角度、84 Glow volumes：

- R5.7.41.3.4.4：3.9605 s
- R5.7.41.3.4.5：2.0351 s
- speedup：約 1.946×
- elapsed reduction：約 48.6%
- `cloud_provenance_call_count`: 84 → 0
- `cloud_handoff_hit_count`: 0 → 84
- detail exact equality：PASS
- summary exact equality：PASS

此離線 benchmark 未包含 CASE 未保存的完整內部 merged route snapshot，因此只證明 handoff/shared-context path 的 deterministic 等價與局部效能，不宣稱 full CASE 一定等比例加速。
