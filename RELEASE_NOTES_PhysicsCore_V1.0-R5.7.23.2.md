# Taiwan Firecloud PhysicsCore V1.0-R5.7.23.2 發行說明

## 版本主旨

**Memory-Safe Aggregation Hotfix**

本版針對實際 Cold/Resume 測試中，13 個太陽高度角全部完成後，程式停留於「彙整民用曙暮光時間軸與矩陣…」且 RSS 約 1.2 GB 的現象進行工程修正。

## 問題根因

R5.7.23.1 在 aggregation 階段會同時保留：

1. `details` 中 13 個角度的大型 per-angle DataFrame；
2. 為 aggregation 建立的 `.copy()`；
3. `pd.concat()` 後的最終大型矩陣；
4. 尚未釋放的各類 V1 frame list。

因此在大型 13-angle CASE 中形成明顯 transient RAM peak。

## 本版修正

- completeness audit 改在 heavyweight frame drain 前建立。
- 新增 memory-safe `_drain_detail_matrix()`：大型 frame 從 `details` 移出後直接形成最終矩陣，不再保留一份 per-angle duplicate copy。
- `pd.concat(..., copy=False)` 降低不必要資料複製。
- V1 evidence frame list concat 後立即 `clear()`。
- 大型 aggregation 群組間執行 `gc.collect()`。
- 將 aggregation 拆成可觀測子階段：幾何、基礎雲體、氣壓/原生雲體、雲光學、光譜/大氣、Formation evidence、Viewing/Tier-2、完整性摘要。
- 每個 aggregation 子階段都寫入 runtime resource telemetry。

## 科學邊界

本版不修改：Formation、Viewing、Glow、Earth Shadow、DirectSolarFraction、六波段 RT、Target Optical Truth、Route Invariance、Tier-2 calibration contract 或任何物理權重。

## Regression

- Working tree：412 passed / 0 failed
