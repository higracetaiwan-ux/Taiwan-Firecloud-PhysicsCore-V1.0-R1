# TWS106 Observer Environment Timeline — `.10.9.4` Offline Validation

## 資料來源

使用 `.10.9.3` TWS106 2026-09-14 sunset CASE 既有：

- `forecast_raw.csv`
- `native_gfs_cloud_columns.csv`
- `event_time_contract.csv`

沒有新增 provider request。

## 產出

- timeline：855 rows
- summary：171 rows
- native snapshot matched rows：270
- native time unmatched rows：585

## Ground Truth 對齊

| 實景時間 | 地點標籤 | 最近 timeline | Δt |
|---|---|---|---:|
| 17:07:49 | 高美 | 17:05:21 | 147 s |
| 17:52:09 | 彰化附近 | 17:50:21 | 107 s |
| 18:02:00 | 高美 | 18:00:21 | 98 s |
| 18:15:52 | 高美 | 18:15:21 | 30 s |
| 18:26:05 | 高美 | 18:25:21 | 43 s |
| 18:26:31 | 彰化附近 | 18:25:21 | 69 s |
| 18:29:03 | 高美 | 18:30:21 | 79 s |
| 18:29:54 | 高美 | 18:30:21 | 28 s |

## 模式與實景的主要 mismatch

使用者實景顯示整段時序均有廣泛低雲／低雲帶；模式 coarse low-cloud 在近場卻偏低：

- 17:05 中心 0–10 km mean 1.67%、10–40 km 4.01%；
- 17:50 中心 0–10 km 1.67%、10–40 km 4.14%；
- 18:00 中心 0–10 km 1.70%、10–40 km 4.16%；
- 18:15 中心 0–10 km 3.20%、10–40 km 3.78%；
- 18:25 中心 0–10 km 4.20%、10–40 km 3.53%；
- 18:30 中心 0–10 km 4.70%、10–40 km 3.41%。

相對地 40–100 km coarse low-cloud 持續較高；18:00→18:25 時 native snapshot 能對時，但仍沒有 0–100 km low-cloud geometry，形成 `COARSE_LOW_CLOUD_PRESENT_NATIVE_3D_NOT_RECONSTRUCTED`。

## Ground Truth 限制

影像可證明 observer view sector 有廣泛低雲，但單視角不能可靠反推每片雲的距離、雲底高度或 COT。彰化同步視角支持「區域性低雲場」判讀，但本版不做 multi-view 3D triangulation。

## 結論

Timeline diagnostic 可有效把 Ground Truth 與 forecast/native evidence 對齊，而且不改 Formation/Viewing/Glow。正式狀態仍需 `.10.9.4` Field CASE 後才能升為 FIELD PASS。
