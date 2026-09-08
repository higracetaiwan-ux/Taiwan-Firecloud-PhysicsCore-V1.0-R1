# Taiwan Firecloud PhysicsCore V1.0-R5.7.23.1 實作狀態

## 已完成

- [x] CAMS global ADS single-flight 維持 production 預設。
- [x] CAMS decoded-route cache write 狀態可觀測。
- [x] CAMS bundle post-process 狀態可觀測。
- [x] Cold Test 跳過非必要 decoded-route 二次 pickle cache。
- [x] Warm/Resume decoded-route cache atomic rename 保留。
- [x] decoded-route 額外 fsync 改為 opt-in。
- [x] Streamlit rerun 自動 reattach 仍存活 detached analysis worker。
- [x] reattach 不啟動重複 analysis worker。
- [x] reattach 保留原始 request。
- [x] 新增 R5.7.23.1 regression tests。
- [x] 完整 pytest：409 passed / 0 failed。

## 科學狀態

本 hotfix 不修改 PhysicsCore 科學輸出。Genuine Liquid-Cloud Full Directional Calibration Pipeline 仍維持 R5.7.23 V3 contract；本環境沒有 `uvspec`，因此 genuine calibrated LUT 仍未生成／未安裝。
