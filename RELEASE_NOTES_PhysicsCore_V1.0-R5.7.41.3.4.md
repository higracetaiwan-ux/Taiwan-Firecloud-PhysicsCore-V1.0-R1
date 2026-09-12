# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4

## Historical GFS AWS Indexed-Range Provider Routing

- 為 GFS 0.25° native `pgrb2` 新增 NOMADS → NOAA AWS `.idx + HTTP Range` transport fallback。
- 同步為 `pgrb2b.0p25` Canvas intermediate-level optical probe 加入相同歷史 fallback。
- fallback 必須使用原本已 frozen 的 GFS run / forecast lead，不會為了找得到資料而換 cycle。
- 只抓指定變數與 pressure levels 的完整 GRIB messages；不下載整個全球 GRIB2 檔。
- HTTP Range 若被忽略而回 200，立即 fail，避免誤抓 full object。
- archive object/index/required native messages 不存在時保持 Missing；禁止 RH/Cloud Fraction 補造 condensate。
- CASE provider audit 新增 transport、selected-message count、range count、downloaded bytes、object/index provenance。
- 不修改 Production/Shadow COT、Formation、Viewing、Twilight Glow、Photography、六波段或 Dynamic Corridor/REZ 科學契約。

## Field trigger
2026-08-30 TWS175 historical replay 中，CAMS 可由快取/歷史鏈正常取得，但 frozen GFS 2026-08-29 18Z f003 在 NOMADS filter 回 HTTP 403，造成 native CLWMR/ICMR 全 Missing。R5.7.41.3.4 將這類「NOMADS window exceeded」改走 AWS historical object transport。

## Release Gate
Working-tree：604/604 PASS；Trial fresh-extract：604/604 PASS；Final fresh-extract：604/604 PASS；1 個既有 pandas FutureWarning，非失敗；Release Gate CLOSED。
