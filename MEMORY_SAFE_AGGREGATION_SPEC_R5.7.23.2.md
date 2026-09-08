# R5.7.23.2 Memory-Safe Aggregation 規格

## 目的

避免 13-angle PhysicsCore 在所有角度完成後，於 aggregate matrix 建置階段同時持有 per-angle originals、copies 與 final concatenated tables，造成 transient RAM peak。

## 核心策略

1. 先建立需要 per-angle detail 的 completeness audit。
2. Heavyweight DataFrame 以 `pop()` 從 `details` 移出。
3. 時間與角度欄位在原 frame 上補齊，不建立 `.copy()`。
4. 使用 `pd.concat(..., copy=False)` 建立 final matrix。
5. concat 後立即清除暫存 frame list。
6. 大型群組完成後主動 GC。
7. `details` 僅保留 UI/metadata/legacy diagnostic 真正需要的內容。

## 不可改變

- 13 個太陽高度角。
- 0.5 km vertical grid。
- CASE evidence coverage。
- Formation / Viewing / Glow 科學分離。
- 六波段 RT。
- Route Invariance。
- Genuine calibrated LUT gate。
