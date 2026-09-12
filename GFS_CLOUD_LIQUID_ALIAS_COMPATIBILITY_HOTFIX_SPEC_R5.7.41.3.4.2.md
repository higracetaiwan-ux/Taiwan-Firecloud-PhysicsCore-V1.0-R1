# R5.7.41.3.4.2 — GFS Cloud-Liquid Alias Compatibility Hotfix

## 目的
2026-08-30 TWS175 歷史 Field CASE 證實 NOMADS 403 後 NOAA GFS AWS `.idx + HTTP Range` fallback 成功，但主 `pgrb2.0p25` subset 取得 ICMR/RWMR/SNMR/GRLE/TCDC/TMP/RH/HGT 時，CLWMR 為 0 層，導致 `MISSING_REQUIRED_CONDENSATE_FIELDS`。

NCEP GRIB2 moisture table 使用 `CLMR` 表示 Cloud Mixing Ratio，而 GFS product inventory 常顯示 `CLWMR`。本版只在 transport/index 與 decoder shortName normalization 層加入同義名稱相容：

- request `CLWMR` 時，AWS `.idx` selector 接受 `CLWMR` 或 `CLMR`;
- ecCodes shortName `clmr` canonicalize 為既有 `CLWMR`;
- pgrb2 與 pgrb2b decoder 同步；
- audit 保存 raw variable counts 與 canonical variable counts。

## 科學不變
- 不把 Missing 當 Zero；
- 不用 ICMR 代替缺失 liquid field；
- 不用 RH / Cloud Fraction 推估 condensate；
- 若 archive 同時沒有 CLMR 與 CLWMR，仍為 Missing；
- Production/Shadow COT、Formation、Viewing、Glow 與 Photography 門檻不變；
- Science baseline 保持 `R5.7.41.2_SHADOW_COT_AB_FROZEN`。
