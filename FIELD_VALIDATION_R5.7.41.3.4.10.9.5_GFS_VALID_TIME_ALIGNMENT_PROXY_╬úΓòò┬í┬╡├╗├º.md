# R5.7.41.3.4.10.9.5 — GFS Valid-Time Alignment Proxy Validation

本報告只重算既有 TWS106 / TWS111 CASE 的 GFS forecast-hour 對齊；不重算雲物理、Formation、Viewing 或 Glow，因此不是 Field PASS。

## TWS106 `.10.9.4`

- 原 CASE GFS cycle：2026-09-14 06Z。
- 舊 resolver：f003 → valid 09:00 UTC（17:00 local）。
- 事件 0°→−6°：10:00:21→10:26:48 UTC。
- `.10.9.5` 同一 cycle：全事件區間最近逐小時 state 為 f004 → 10:00 UTC。
- 舊最大時間偏差：約 5208 s（86.8 min）。
- 新最大時間偏差：約 1608 s（26.8 min）。

## TWS111 `.10.9.3`

- 原 CASE GFS cycle：2026-09-14 00Z。
- 舊 resolver：f009 → valid 09:00 UTC（17:00 local）。
- 事件 0°→−6°：10:00:39→10:27:04 UTC。
- `.10.9.5` 保留原 00Z cycle 時，最近逐小時 state 為 f010 → 10:00 UTC。
- 舊最大時間偏差：約 5224 s（87.1 min）。
- 新最大時間偏差：約 1624 s（27.1 min）。

## 結論

兩個既有 CASE 都證明 blanket 3-hour rounding 會在日落事件把 native condensate 綁到約 1 小時前的 state。`.10.9.5` 把 valid-time 偏差壓回最近逐小時輸出的合理範圍，但仍必須正式重跑 CASE 才能知道 hourly-aligned CLWMR/ICMR 是否仍為零。
