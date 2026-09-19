# CAMS Adaptive Same-Request-ID Reattach Spec — R5.7.41.3.4.10.30.18.2

Contract: `R5.7.41.3.4.10.30.18.2_ADAPTIVE_QUEUE_RUNNING_SAME_REQUEST_ID_REATTACH_V1`

1. Trigger only after `TIMEOUT_DEFERRED` with durable `ads_request_id` and recovery eligibility.
2. Applies to both `CAMS_ADS_QUEUE_GRACE_EXCEEDED` and `CAMS_ADS_RUNNING_GRACE_EXCEEDED`.
3. Recovery child must use `reattach_only=True` and may only `get_remote(request_id)`.
4. Fresh submit is forbidden during reattach recovery.
5. Attempts are bounded by `FIRECLOUD_CAMS_DEFERRED_REATTACH_COUNT`.
6. If recovery still does not complete, result remains Missing / `TIMEOUT_DEFERRED`.
7. A deferred timeout must not trigger adaptive geographic subdivision.
8. No frozen-science or Step3Q provenance rule is changed.
