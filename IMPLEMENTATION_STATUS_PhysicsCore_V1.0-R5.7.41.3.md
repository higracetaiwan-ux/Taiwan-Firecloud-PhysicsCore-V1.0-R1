# Implementation Status — PhysicsCore V1.0-R5.7.41.3

## 已完成
- Shared Scenic Spot Registry V2.2（187 unique GPS spots）
- `site_id` / location provenance
- 區域＋可搜尋景點 selector
- 自訂座標 fallback
- 舊 request location-source backward compatibility
- CASE Shadow Validation manifest / cohort / Ground Truth / runtime artifacts
- Science baseline freeze guard
- Offline multi-CASE cohort aggregation tool
- CASE filename site-id handoff

## 凍結未改
- Production COT = legacy source
- Shadow COT = diagnostic candidate only
- Production switch = False
- COT / Formation promotion = False
- Formation / Viewing / Twilight Glow / Photography science

## Release Gate
- Working-tree regression：589/589 PASS
- FULL-CLEAN fresh-extract regression：589/589 PASS
- 1 個既有 pandas FutureWarning，非失敗
- Gate：CLOSED

## 下一步
部署本版並跑一次 Online CASE 驗證新 selector 與 collection artifacts；之後開始累積 sunrise / sunset Shadow CASE cohort。
