# FIELD VALIDATION — R5.7.41.3.4.10.22

事件：2026-09-17 sunrise  
案例：TWS091 日月潭朝霧碼頭 + TWS100 合歡山北峰

## 結論

`V1.0-R5.7.41.3.4.10.22 FIELD PASS`

兩個 CASE 均：

- runtime：`WARM_PRODUCTION`
- worker：COMPLETED / exit code 0
- Analysis Integrity：124 PASS / 1 NOT_APPLICABLE / 0 FAIL
- CASE Integrity：101/101 PASS
- manifest：175/175 members present / byte-size match / SHA256 match
- Step 3I evidence：12 rows
- Step 3I gate：1 row
- Step 3I contract：`FIRECLOUD_ICE_WYSER_YANG_POPULATION_BRIDGE_V1`

TWS100 execution elapsed 約 `482.64 s`；TWS091 約 `449.48 s`。

Step 3I evidence / gate 在 CASE 與 release artifacts byte-identical；contract 解析後 semantic differences = 0。兩個案例都維持 Dmax/habit/roughness/tau/Formation promotion fail-close。

因此 `.10.22` 升為正式 FIELD baseline，下一版可進 Step 3J diagnostic PSD × Yang/Bi Cext bulk integration。
