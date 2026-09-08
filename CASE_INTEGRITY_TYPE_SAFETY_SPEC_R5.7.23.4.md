# R5.7.23.4 CASE Integrity Type-Safety 規格

## 問題

Cold Test 實測中，CAMS `NATIVE_AEROSOL_532NM_PRESSURE_LEVEL` 觸發 90 秒 ADS wall-clock timeout。分析本體已完成 13/13 路徑預報內插，但在 `build_analysis_integrity_audit()` 階段因 CAMS request-audit 欄位混合字串、浮點數與 NaN，row-wise `" ".join` 觸發 `TypeError: sequence item ... expected str instance, float found`，導致 analysis worker 不必要地 FAILED。

## 修正契約

1. Provider / CASE integrity audit 必須對 heterogeneous schema type-safe。
2. 任一文字比對欄位在 join 前逐 cell 正規化：NaN → 空字串，其餘 → `str(value)`。
3. CAMS role、GFS completeness 與一般文字 token audit 共用同一安全文字合併 helper。
4. CAMS `CAMS_ADS_TIMEOUT` 是資料可用性狀態，不是 analysis process crash 條件。
5. Timeout / Missing 仍依原有完整性規則輸出 PASS/WARN/FAIL，不得造假資料或把 Missing 改成 Clear/Zero。
6. 不修改 Formation、Viewing、Glow、六波段 RT、Route Invariance、Tier-2 calibration 或 CAMS 90 秒 watchdog。

## CASE 檔名

CASE ZIP 下載檔名不再硬編碼 `R5.7.23`，改由 runtime `__version__` 產生完整 hotfix 版本，以避免檔名與 CASE 內部版本不一致。
