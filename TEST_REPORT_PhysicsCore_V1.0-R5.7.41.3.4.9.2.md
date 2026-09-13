# TEST REPORT — PhysicsCore V1.0-R5.7.41.3.4.9.2

## 結果
- Targeted tests: 13/13 PASS
- Full regression: 647/647 PASS
- Warning: 1 個既有 pandas FutureWarning，非失敗

## 新增驗證
1. grouped precipitation integrator 對 legacy integrator exact-equivalent。
2. horizontal-support grouping 保持 vertical cell 原始順序。
3. ray sampling call count = relevant horizontal-support count，且小於 relevant pressure-level cell count。
4. prepared context 與 direct context science DataFrame `check_exact=True`。
5. `.3.4.9.1` Field CASE science outputs 與 `.3.4.9` 保持 byte-for-byte equivalent；`.3.4.9.1` runtime hypothesis 被 Field evidence 否決。

## Synthetic benchmark
25 hPa 間隔、多垂直層 synthetic native hydrometeor volume：grouped core integrator 約 13× faster than legacy core integrator。僅用來證明結構性消除重複運算，不代表 Streamlit Cloud Field speedup。

## Release gate
需由最終 FULL-CLEAN ZIP fresh-extract 再跑 647/647 PASS 後才可交付。
