# R5.7.29.1 Viewing Precipitation Spool Handoff 規格

## 問題

R5.7.29 已在 native GFS merge 後建立 `viewing_route_snapshot`，但 final
aggregation 先執行 `AngleFrameSpool.cleanup()`，之後才嘗試 drain 新增的
snapshot family。真實 CASE 因此出現：

- GFS `RWMR / SNMR / GRLE = READY`
- eligible Viewing targets：110
- `v1_viewing_precipitation_evidence.csv`：0 rows
- Viewing Full RT completeness：0%
- Analysis Integrity 仍為 PASS

## 修正契約

1. `viewing_route_snapshot` 必須在 native GFS merge 後寫入 spool。
2. final aggregation 必須先 drain `viewing_route_snapshot`，才可 cleanup spool。
3. precipitation evidence 必須交給 pre-export Analysis Integrity。
4. 每個 eligible `time + solar_altitude_deg + canvas_id` 必須有一列 precipitation
   evidence；local/invalid geometry 亦輸出明確 unresolved row。
5. 當 GFS completeness 宣告 RWMR、SNMR、GRLE 全部 READY，空表、缺 target row
   或 `VIEW_PRECIPITATION_VOLUME_UNRESOLVED` 必須是 hard FAIL。

## 不變項目

本版不更改 hydrometeor extinction、particle radius/density、六波段 grey Tier-1
模型、Viewing Full RT 四 component 閘門、Formation、Glow、Photography、角度、
route resolution、CAMS temporal contract 或 Forecast／Observation 分離。

