# Release Notes — R5.7.41.3.4.10.29

## Step 3P Full-Spectral Source Capability Qualification
- 新增 `firecloud/ice_microphysics_yang_full_spectral_source_qualification.py`。
- 新增 authoritative Yang/Bi 396-wave source readiness gate。
- 新增 RRTMG SW band 24/25 spectral-domain coverage qualification。
- source bytes 缺失時 deterministic fail-close，不補值、不下載、不從六波段 LUT 推造。
- 新增 model / CASE archive / integrity handoff。
- Frozen Science 與 production gates 不變。

## Regression
Working tree：927/927 PASS；1 個既有 pandas FutureWarning。
