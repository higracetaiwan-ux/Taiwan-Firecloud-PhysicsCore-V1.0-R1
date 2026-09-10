# Taiwan Firecloud PhysicsCore V1.0-R5.7.38 發行說明

## 本版主題

**CAMS Post-success Download Recovery**。

R5.7.37 field CASE 證明 ADS remote job 可能已 `successful`，但下載節點暫時回傳 502，導致 client downloader 進入約 120 秒 retry sleep。R5.7.38 把「遠端工作等待」與「成功後檔案下載」正式拆成兩個 runtime phase。

## 主要修改

- 保留 R5.7.34 Stateful request ID / request fingerprint / reattach 機制。
- remote success 後，優先以同一 request ID 重新取得 Results/location。
- 對 408/429/500/502/503/504 與連線錯誤做有界 retry。
- 預設 4 attempts，2 秒起始 backoff，12 秒最大 backoff。
- server `Retry-After` 不得突破本地 12 秒上限。
- 每次 retry 都重新取得 Results/location，不重送 CAMS job。
- download URL 不保存到 journal 或 CASE。
- exhausted download failure 仍標記 recovery eligible，下一次 analysis 可 reattach 同一 successful remote job。
- 新增完整 download telemetry 與 Integrity guard。

## 不變項目

- 13 個太陽高度角不變。
- 550/575/600/650/700/750 nm 六波段不變。
- Formation / Viewing / Twilight Glow 三軌不變。
- R5.7.37 Near-Surface Molecular Boundary Closure 與 10 m tolerance 不變。
- CAMS O₃、AOD、native 3D aerosol、SSA/g 物理不變。

## 程式驗證

開發 working-tree regression：**542/542 PASS**。

FULL-CLEAN 預封包解壓後 regression：**542/542 PASS**。

正式 FULL-CLEAN release gate 已關閉；封包內不得包含 `__pycache__`、`.pytest_cache`、`.pyc` 或 `.pyo`。

## Field Validation

R5.7.38 需要新 CASE 驗證。普通無 5xx 的 CASE 可確認 telemetry/schema；真正的 download recovery FIELD CLOSED 最好再捕捉一次 transient download failure，確認 retry 使用同一 request ID 且不再出現固定 120 秒 stall。
