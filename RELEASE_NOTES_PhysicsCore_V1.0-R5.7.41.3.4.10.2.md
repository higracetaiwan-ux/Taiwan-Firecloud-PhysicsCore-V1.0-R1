# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.2

## 名稱
Twilight Glow Molecular Numeric Route Context

## 來源
直接延續 `V1.0-R5.7.41.3.4.10.1 FULL-CLEAN`；science baseline 維持 `R5.7.41.2_SHADOW_COT_AB_FROZEN`。

## Field evidence
`.3.4.10.1` TWS134 CASE：Observer Spectral Extinction 11.765 s，較 `.3.4.10` TWS106 的 21.376 s 下降約 45%；`.3.4.10.1` Field PASS。Glow 新第一大戶為 Volume Assembly 25.414 s。

## 變更
- `firecloud/twilight_glow.py` 新增 Glow molecular numeric route context。
- 每 time/angle/direction/distance 僅整理一次 T/P profile 與 lower-boundary metadata。
- Rayleigh observer path、local molecular state、molecular lower-boundary diagnostics 改讀 immutable numeric arrays。
- Rayleigh/local T/P context與 HITRAN gas-species readiness 分離，保留 legacy availability contract。

## 不變
不改 Rayleigh/HITRAN 公式、六波段、observer LOS geometry、10 m lowest-endpoint tolerance、1 m quantization、ML137 near-surface bridge、Missing semantics、Formation、Viewing、Glow interpretation、Photography、Earth Shadow 或 Production/Shadow COT。

## 驗證
- TWS134 actual-case：1092/1092 Rayleigh/local/boundary exact-equivalent。
- Actual-case molecular helper benchmark：約 4.07 s → 0.30 s（約 13.7×）；僅離線 benchmark。
- Full regression：659/659 PASS（1 existing pandas FutureWarning）。
- Field gate：OPEN；等待 `.3.4.10.2` CASE。
