# `.10.9.6` TWS106 Timeline Provider-Valid-Time Offline Proxy

使用 `.10.9.5` 正式 CASE 的 `forecast_raw.csv`、`event_time_contract.csv`、`native_gfs_cloud_columns.csv`，並將已知 provider `gfs_valid_time_utc=2026-09-14T10:00:00Z` 注入 `.10.9.6` timeline helper 做離線驗證。

結果：
- point rows：2205（49 time steps × 45 route points）
- summary rows：441
- window：T−180→T+60 / 5 min
- matched native rows：45
- unmatched native rows：2160
- matched native reference time 只剩 **一個真正 provider state：10:00 UTC / 18:00 local**

相較 `.10.9.5` CASE 原 timeline 的 270 matched rows / 6 個 angle-derived reference times，本版移除了「同一 f004 state 被多個 angle timestamp 偽裝成多 native snapshots」的 provenance 誤差。

此修正只影響 observer diagnostic evidence handoff；不改 Formation / Viewing / Glow。
