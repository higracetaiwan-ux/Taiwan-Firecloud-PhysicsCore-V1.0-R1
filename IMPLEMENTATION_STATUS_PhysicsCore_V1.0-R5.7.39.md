# Taiwan Firecloud PhysicsCore V1.0-R5.7.39 實作狀態

## 已完成

- GFS `pgrb2b.0p25` intermediate pressure-level native condensate probe provider。
- 0–100 km route-point request scope。
- Canvas fixed vertical-envelope evidence binding。
- CLWMR/ICMR/TCDC/TMP/HGT decode 與 route merge。
- `POSITIVE / ZERO / MISSING` condensate state。
- `NATIVE_CONDENSATE_POSITIVE / CF_CLOUD_CONDENSATE_ZERO / OPTICS_MISSING` evidence semantics。
- probe summary aggregation。
- CASE export：probe / summary / request audit。
- API efficiency 與 runtime cache provenance 接線。
- `CANVAS_OPTICAL_TRUTH_PGRB2B_PROBE_CONTRACT` Integrity guard。
- Integrity 禁止 probe 輸出 target COT / target optics readiness / Formation promotion 欄位。

## Regression

- Focused：**9/9 PASS**。
- Full working tree：**551/551 PASS**。

## 尚待

- FULL-CLEAN release gate。
- R5.7.39 真實 CASE field validation。
- 根據 field evidence 決定是否啟動 Canvas Optical Truth Phase 2。

## 明確不處理

本版不解算 COT、不改 Formation、不融合垂直不重疊的 IFS/GFS 雲體、不以 RH/cloud fraction 造 condensate/COT。
