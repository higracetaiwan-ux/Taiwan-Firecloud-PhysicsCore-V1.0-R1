# R5.7.24 Runtime Reliability / Memory Containment 規格

## 目的

R5.7.24 將長時間分析的「完成性」視為正式工程契約。程式可以慢，但不得因 UI polling、可回收 heap、前端 rerun 或單一 provider timeout 而不必要地失去整個分析。

## Worker / UI 邊界

- Physics analysis 由獨立 subprocess 執行。
- Streamlit 前端不得用長時間 blocking loop 等待 worker。
- UI 僅讀取 progress snapshot，週期性 rerun/fragment 更新。
- 仍存活的 worker 不得因頁面 reload 被重複啟動。

## Recovery durability

每個 job 有 master journal、per-job journal 與 attempt progress 三層可重建狀態。attempt stdout/stderr 必須隔離保存。

若整個 hosting container 被銷毀，本機檔案系統仍可能消失；這超出 local durability 能保證的範圍。若後續證實平台會頻繁換 container，才升級外部 persistent store。

## Memory containment

### Route snapshots

完整 13-angle route snapshots 不可同時常駐 RAM。預先內插後立即寫入 local ephemeral spool；每個 angle 只取一次。

### Per-angle evidence

大型 evidence 不可僅為 final CASE aggregation 而留在 `details`：

- cloud voxel families
- gas profile
- aerosol spectral/native snapshots
- spectral RT frames
- Viewing route snapshot

完整性 audit 應先產生 compact summary，再釋放 full frame。

### UI details

`details.snapshot` 僅保留 cross-section UI 真正需要欄位，不得把完整 provider frame 帶入最終 result。

### Native allocator

每角度邊界允許 best-effort `malloc_trim(0)`；不支援 glibc 的平台必須安全退化為單純 GC，不得影響 physics。

### Provider cache release

所有 angles 完成後，final aggregation 前清除已不再需要的 provider in-memory caches。Persistent provider cache 檔案不受影響。

## 禁止的「記憶體優化」

不得為降低 RSS 而：

- 減少 13 個太陽角度
- 把 0.5 km 垂直解析度改粗
- 刪減六波段
- 將 Missing 當零/晴空
- 移除 Formation / Viewing / Tier-2 evidence
- 改動 Route Invariance

## 驗收

1. Regression 全綠。
2. 真實 Cold Test 能完整跑至 CASE。
3. `runtime_resource_telemetry.csv` 應能看到 `ROUTE_SNAPSHOTS_SPOOLED`、`ANGLE_HEAVY_EVIDENCE_SPOOLED`、`POST_ANGLE_PROVIDER_CACHE_RELEASE`。
4. 與 R5.7.23.4 相同案例比較核心 Formation / Viewing / Tier-2 outputs 不得 drift。
5. RSS 曲線應較 R5.7.23.4 明顯收斂；若仍逼近平台限制，再進下一層 process isolation，而不是犧牲科學解析度。
