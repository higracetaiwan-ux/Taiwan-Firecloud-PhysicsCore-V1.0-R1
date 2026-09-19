# Taiwan Firecloud PhysicsCore V1.0 — FIELD Validation

## R5.7.41.3.4.10.30.18.1 — TWS100 — 2026-09-20 sunrise

**Result: FIELD FAIL**

### Root cause
- CASE ZIP / manifest 均完整，worker `COMPLETED / exit_code=0`。
- `analysis_integrity_audit`: `124 PASS / 7 WARN / 4 ALLOWED_EMPTY / 3 NOT_APPLICABLE / 2 FAIL`。
- `case_integrity_audit`: `138 PASS / 2 FAIL`。
- hard failure: `CAMS_AEROSOL_SPECTRAL_PAYLOAD_VALIDITY=0.0`（expected >=0.95）。

四條 aerosol role：
- `PRESSURE_LEVEL_CHEMISTRY_OPTICS_BUNDLE`
- `NATIVE_AEROSOL_532NM_PRESSURE_LEVEL`
- `AEROSOL_SCATTERING_COLUMN_PROPERTIES`
- `SPECTRAL_COLUMN_AOD`

皆在 ADS `accepted` queue phase 約 75–77 s 後觸發 `CAMS_ADS_QUEUE_GRACE_EXCEEDED → TIMEOUT_DEFERRED`。

`.18.1` 的 same-request-ID reattach 實作位於 serial scheduler；真實 WARM_PRODUCTION 使用 `WHOLE_ROUTE_FIRST_ADAPTIVE_SUBTILING` / `_fetch_cams_role_adaptive()`，該 path 對 `TIMEOUT_DEFERRED` 仍直接 return，因此沒有 reattach telemetry，也沒有同-run recovery。

### Provenance
Step3Q `.10.30.18 / V1_18` artifacts 正常，Fu96 Band24 inverse re-averaging barrier 不受影響。此次 FAIL 是 CAMS runtime scheduler coverage 問題，不是 frozen science 或 provenance failure。

### Formal status
`R5.7.41.3.4.10.30.18.1 FIELD FAIL — ADAPTIVE_SCHEDULER_DEFERRED_REATTACH_NOT_APPLIED`
