# `.10.9.5` TWS106 2026-09-14 Sunset Field Validation

## 結論

**GFS Hourly Native Valid-Time Alignment：FIELD PASS。**

- version：`1.0.0-R5.7.41.3.4.10.9.5`
- job：COMPLETED
- GFS cycle/lead：06Z f004
- target：10:00:21.746 UTC
- valid：10:00:00 UTC
- offset：−21.746 s
- `GFS_NATIVE_VALID_TIME_ALIGNMENT = PASS`
- CASE Integrity：36/36 PASS

## 低雲根因進度

修正 f003→f004 後，0–100 km native low-cloud 仍未恢復：

- native voxel rows：21060
- CLWMR > 0：0
- ICMR > 0：0
- native TCDC > 0：0
- native columns：585
- vertical completeness：全部 1.0
- LWP/IWP proxy：全部 0

因此 `.10.9.5` 證明「舊版一小時 stale state」是實際 bug，但它不是 TWS106 Ground Truth 低雲 mismatch 的唯一原因。

## 新發現的 diagnostic provenance 問題

`.10.9.5` 繼承 `.10.9.4` Timeline 行為：同一個 f004 provider state 在多角度重用後，以 angle analysis time 當作多個 native reference times。這不改 Physics，但會讓 timeline 看起來像有多個不同 native snapshots。

`.10.9.6` 改以 provider `gfs_valid_time_utc` 做 native matching。

## Runtime

- TOTAL_ANALYSIS_CORE：約 542.86 s
- worker elapsed：約 569.63 s
- CAMS_PREFETCH_TOTAL：約 322.09 s

主要耗時仍是 CAMS provider latency，不是 GFS valid-time hotfix 或 Observer Timeline。
