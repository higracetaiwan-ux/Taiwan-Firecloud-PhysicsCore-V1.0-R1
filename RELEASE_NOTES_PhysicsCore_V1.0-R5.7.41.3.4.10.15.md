# RELEASE NOTES — V1.0-R5.7.41.3.4.10.15

## Ice Optics Phase 2 Step 3B — GFS v16 Exact Scheme Pinning Evidence Gate

新增 `firecloud/ice_microphysics_gfsv16_scheme_pin.py`，正式區分「公開可重現 GFS v16-compatible scheme evidence」與「NCEP production binary exact provenance」。

新增 CASE artifacts：
- `ice_microphysics_gfsv16_scheme_pin_evidence.csv`
- `ice_microphysics_gfsv16_scheme_pin_gate.csv`
- `ice_microphysics_gfsv16_scheme_pin_contract.json`

新增 Analysis Integrity gates：
- `ICE_MICROPHYSICS_GFSV16_SCHEME_PIN_EVIDENCE_PRESENT`
- `ICE_MICROPHYSICS_GFSV16_SCHEME_PIN_CONTRACT_FREEZE`
- `ICE_MICROPHYSICS_GFSV16_SCHEME_PIN_FAIL_CLOSED`

CASE Archive Integrity 同步要求三個新 artifacts。

沒有新增 Dmax conversion、PSD reconstruction、habit default、roughness default 或 production promotion。

Regression：796/796 PASS。
