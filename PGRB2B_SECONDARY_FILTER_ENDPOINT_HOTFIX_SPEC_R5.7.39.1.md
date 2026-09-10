# R5.7.39.1 pgrb2b Secondary Filter Endpoint Hotfix

## 問題
R5.7.39 已正確建立 `pgrb2b.0p25` intermediate pressure-level probe，但 URL routing 錯誤使用 `filter_gfs_0p25.pl`，真實 CASE f003/f006 均得到 HTTP 500。

## 修正
- `pgrb2.0p25` 主產品：維持 `filter_gfs_0p25.pl`。
- `pgrb2b.0p25` Secondary Parameters：改用 `filter_gfs_0p25b.pl`。
- file / dir / bbox / variables / pressure levels 不變。
- probe 仍 diagnostic-only。
- 不改 target COT readiness。
- 不改 Formation / Viewing / Glow / Photography。
- 不允許 RH/cloud fraction 生成 condensate/COT。
- Missing 仍為 Missing。

## Regression Guard
新增 endpoint regression：任何 `pgrb2b` request 若回到 `filter_gfs_0p25.pl` 即 FAIL。
