# CAMS Bounded Same-Request-ID Reattach Observation Window — R5.7.41.3.4.10.30.21

## 背景
`.10.30.20` TWS100 FIELD 首次實際觸發 adaptive same-request-ID reattach。兩個 native 3-D aerosol roles initial deadline 後進 reattach，但再次使用完整 provider deadline，兩條都再 timeout，明顯拉長總 runtime。

## 新規則
`_deferred_reattach_deadline_seconds(initial_deadline_seconds)`：
- explicit env override：`FIRECLOUD_CAMS_DEFERRED_REATTACH_DEADLINE_SECONDS`
- override clamp：0.2 s 至 initial deadline
- default：`min(initial, max(20, min(75, initial*0.35)))`
- 210 s → 73.5 s
- 90 s → 31.5 s
- 1 s → 1 s

## 不變的可靠性契約
- reattach-only
- same original ADS request ID
- fresh submit forbidden
- duplicate ADS jobs forbidden
- reattach timeout → Missing
- Missing ≠ Clear ≠ Zero
- Frozen Science 不變

## Telemetry
新增：
- `deferred_initial_deadline_seconds`
- `deferred_reattach_deadline_seconds`
- `deferred_recovery_contract=R5.7.41.3.4.10.30.21_BOUNDED_SAME_REQUEST_ID_REATTACH_OBSERVATION_WINDOW_V1`
