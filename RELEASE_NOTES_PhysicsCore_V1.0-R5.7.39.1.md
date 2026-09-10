# Taiwan Firecloud PhysicsCore V1.0-R5.7.39.1 發行說明

## 主題
GFS pgrb2b Secondary Parameter Grib Filter Endpoint Hotfix。

R5.7.39 真實 2026-09-10 sunset CASE 顯示，兩個 pgrb2b probe request（f003/f006）都得到 HTTP 500，probe evidence 與 summary 為空。Root cause 是 secondary product `pgrb2b.0p25` 誤用主 product endpoint `filter_gfs_0p25.pl`。

R5.7.39.1 修正為 NOAA/NCEP Secondary Parameters endpoint：

`https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25b.pl`

本版不改任何 Canvas optical science、target COT、Formation、Viewing、Glow、六波段、13 angles 或 10 m molecular tolerance。

## 驗證
- Focused probe/hotfix tests：10/10 PASS。
- Full working-tree regression：552/552 PASS。
- Field validation：需要 R5.7.39.1 新 CASE 實際確認 pgrb2b rows 可取得；R5.7.39 的空 probe 不算 condensate-zero evidence。
