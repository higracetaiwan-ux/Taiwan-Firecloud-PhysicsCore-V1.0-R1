# Taiwan Firecloud PhysicsCore V1.0-R5.7.23.4 發行說明

## 主題

**CASE-Integrity Type-Safety Hotfix + CASE Versioned Filename Fix**

## 修正

- 修正 `firecloud/case_integrity.py::_cams_role_success()` 在 CAMS request-audit 欄位含 float / NaN 時可能觸發 `TypeError: expected str instance, float found`。
- 新增共用 type-safe 文字欄位合併 helper，CAMS role、GFS completeness、文字 token audit 均不再依賴可能受 Pandas dtype 影響的 `agg(" ".join)`。
- 明確保證 CAMS `CAMS_ADS_TIMEOUT` 只會留下 Timeout/Missing 證據，不可讓 analysis worker 因 audit schema 型別而崩潰。
- CASE ZIP 檔名改由 runtime `__version__` 產生，hotfix 版本與檔名保持一致。
- 完整保留 R5.7.23.3 CAMS live telemetry、R5.7.23.2 Memory-Safe Aggregation、R5.7.23 Runtime Hardening 與 Liquid Full Directional Calibration Pipeline。

## 科學契約

本 hotfix 不修改：Formation / Viewing / Glow、Earth Shadow、DirectSolarFraction、六波段、Missing 語義、Route Invariance、Tier-2 directional geometry、CAMS 90 秒 watchdog 或 calibration gate。

## Genuine LUT 狀態

`CALIBRATED DIRECTIONAL LUT NOT INSTALLED` / `NOT_YET_GENERATED_EXTERNAL_RT_REQUIRED` 維持不變。
