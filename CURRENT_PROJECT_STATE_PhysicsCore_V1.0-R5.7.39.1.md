# Taiwan Firecloud PhysicsCore — Current Project State
## V1.0-R5.7.39.1

目前主線：Canvas Optical Truth Phase 1 / GFS pgrb2b intermediate-level native condensate evidence probe。

### 最新狀態
- R5.7.37 Near-Surface Molecular Boundary：FIELD CLOSED。
- R5.7.38 CAMS normal download telemetry：FIELD PASS；真實 transient download recovery branch 仍 OPEN。
- R5.7.39 pgrb2b probe：真實 CASE 發現 provider endpoint routing bug，f003/f006 HTTP 500，空 probe 不得視為 condensate zero。
- R5.7.39.1：修正 secondary filter endpoint，science 不變。

### 下一個 CASE 必查
1. `gfs_canvas_optical_probe_request_audit.csv` f003/f006 是否 READY。
2. `v1_canvas_optical_native_probe.csv` 是否產生 rows。
3. 125/175/225...925 hPa 中落入固定 Canvas vertical envelope 的 CLWMR/ICMR 是否 positive / zero / Missing。
4. probe 仍不得直接改寫 target COT / Formation。
