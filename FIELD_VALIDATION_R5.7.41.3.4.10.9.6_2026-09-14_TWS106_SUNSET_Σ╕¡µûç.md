# `.10.9.6` TWS106 2026-09-14 Sunset Field Validation

## 結論

**FIELD PASS**。

- Job COMPLETED
- worker elapsed：632.94 s
- Analysis Integrity：66 PASS / 5 WARN / 4 ALLOWED_EMPTY / 2 NOT_APPLICABLE / 0 FAIL
- CASE Integrity：38/38 PASS
- GFS 06Z f004 valid-time alignment PASS（offset −21.746 s）

## Near-field GFS source attribution

0–100 km decoded source 1080 rows：
- `SOURCE_CONDENSATE_EXACT_ZERO`：990
- `SOURCE_CONDENSATE_MISSING`：90
- positive below threshold：0
- positive at/above threshold：0

9 個 low-layer summary 全部為 `LOW_LAYER_SOURCE_NATIVE_PRESSURE_LEVELS_EXACT_ZERO`。

因此現場明顯低雲與 GFS native 的落差已可歸因為 source forecast underrepresentation；不是 PhysicsCore threshold / interpolation / cloud-column assembly 把正 condensate 刪掉。

## Runtime

主要耗時：
- CAMS Prefetch 254.16 s
- All-angle physics 184.52 s
- Aggregation 66.38 s
- DWD Secondary Native Optics 64.58 s
- Observer Timeline 11.23 s

CAMS `SPECTRAL_COLUMN_AOD` 單一 request 47.275 s；而 `AEROSOL_SCATTERING_COLUMN_PROPERTIES` 同時已要求相同 550/645/670/800 nm AOD，因此列為下一版 exact-source reuse 優先項目。
