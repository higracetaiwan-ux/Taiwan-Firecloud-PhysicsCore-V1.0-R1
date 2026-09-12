# Taiwan Firecloud PhysicsCore — Current Project State

## V1.0-R5.7.41.3.4

本版為 Historical GFS AWS Indexed-Range Provider Routing。

### Field trigger
2026-08-30 Sunrise / TWS175 歷史 CASE 證明 CAMS 歷史鏈可用，但 frozen GFS `2026-08-29 18Z / f003` 在 NOMADS 0.25° GRIB Filter 回 HTTP 403，造成 native CLWMR/ICMR、Cloud Optics 與 Shadow COT evidence 缺失。

### 修正
- Primary GFS pgrb2：NOMADS 失敗後，保持同 run/lead 改讀 NOAA AWS GFS object。
- Canvas pgrb2b probe：同樣加入 AWS historical fallback。
- AWS 透過 `.idx` 只選指定 pressure-level messages，以 HTTP Range 取得完整 GRIB2 message spans。
- Range 被忽略（HTTP 200）時拒絕接收，避免下載整個全球檔。
- archive/object/index/required native messages 真缺時仍保持 Missing。

### Science baseline
`R5.7.41.2_SHADOW_COT_AB_FROZEN`

### 不改動
Production/Shadow COT semantics、Formation、Viewing、Twilight Glow、Photography、六波段、Earth Shadow、Canvas/blocker、Dynamic Corridor/REZ、Missing≠Clear 規則均不改。

### Historical replay target
部署本版後重新跑 `2026-08-30 Sunrise / TWS175 三仙台`。預期同一 `2026-08-29 18Z / f003` 不再因 NOMADS 403 直接失去 native microphysics；若 AWS archive object 可用，應在 CASE audit 中看到 `OK_AWS_IDX_RANGE`。

### Shadow cohort
現有正式 cohort #001–#008 保持不變；2026-08-30 provider-failure CASE 保留為 Historical Replay Provider Failure Case H001，不計入正式 Shadow cohort。

### Release Gate
Working-tree regression：604/604 PASS；Trial fresh-extract：604/604 PASS；Final fresh-extract：604/604 PASS；1 個既有 pandas FutureWarning，非失敗；Release Gate：CLOSED。
