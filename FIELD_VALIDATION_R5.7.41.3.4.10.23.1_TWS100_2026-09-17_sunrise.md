# FIELD Validation — R5.7.41.3.4.10.23.1 / TWS100 / 2026-09-17 sunrise

結論：**FIELD PASS**。

- Analysis worker：COMPLETED / exit code 0 / WARM_PRODUCTION。
- worker elapsed：約 497.15 s。
- Analysis Integrity：126 PASS / 1 NOT_APPLICABLE / 0 FAIL。
- CASE Integrity：107/107 PASS。
- Manifest：178/178 artifacts present；178/178 size match；178/178 SHA256 match。
- 實際觸發 `AEROSOL_SCATTERING_COLUMN_PROPERTIES = TIMEOUT_DEFERRED`；durable checkpoint 已正確保存 terminal `TIMEOUT_DEFERRED`、exit code 1 與 `CAMS_ADS_QUEUE_GRACE_EXCEEDED`，證明 `.10.23.1` checkpoint reconciliation 對不同 CAMS role 通用。
- Step 3J evidence/gate stable serialization PASS。
- positive-IWP runtime 仍保持 Dmax/habit/roughness/k_ext/tau fail-close；沒有 production promotion。

因此 `.10.23.1` 為 `.10.24` 的正式 FIELD baseline。
