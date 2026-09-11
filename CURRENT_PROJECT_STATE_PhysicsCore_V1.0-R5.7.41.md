# Taiwan Firecloud PhysicsCore — Current Project State
## V1.0-R5.7.41

**日期：2026-09-11**

## 正式基線
R5.7.40.1 已完成 FULL-CLEAN release，並於 2026-09-11 sunset CASE 驗證：
- Vertical Conflict Integrity Handoff：Targeted Field PASS。
- CAMS 第二次相同 CASE durable reattach：6/6 原 request ID 成功續接。
- Analysis Integrity：66/66 PASS。
- CASE Integrity：23/23 PASS。
- R5.7.34 timeout→later reattach branch：Field CLOSED。
- R5.7.38 remote-success 後 download 408/429/5xx retry branch：仍 Field OPEN（本 CASE 未觸發）。

## R5.7.41 主題
Canvas Optical Truth Phase 2A / Target Vertical Microphysics Overlap。

### 已凍結不變
- Formation ≠ Viewing ≠ Twilight Glow。
- 六波段 550/575/600/650/700/750 nm。
- Runtime 0→-6°、0.5°間隔；核心火燒雲窗 0→-4°。
- Missing ≠ Clear ≠ Zero ≠ N/A。
- RH / cloud fraction 不得生成 τ / COD / COT。
- <2 km 低雲不是 Formation Canvas。
- 0–100 km 為 Formation Canvas domain。
- 300–350 km blocker 依 ray height + vertical extent + optical thickness。
- Near-surface molecular tolerance 10 m 不放寬。
- Himawari 僅 observation / retrospective。

## R5.7.41 實作狀態
已完成：
- pgrb2 + pgrb2b native vertical merge。
- target-envelope sample position。
- boundary-only / interior support 分離。
- expected supplement Missing preservation。
- vertical bracket / known coverage / max gap。
- COT assumed-r_eff diagnostic scaffold。
- direct conflict blocks COT diagnostic。
- no COT / Formation promotion。
- CASE outputs + Analysis Integrity guard。
- Offline CASE Replay。

## 離線 CASE -2 replay
988 vertical conflict rows / 58 unique canvases：
- 979 `NO_NATIVE_CONDENSATE_SUPPORT`
- 9 `BOUNDARY_ONLY_NATIVE_CONDENSATE_SUPPORT`
- 0 interior positive support

這 9 筆全部是舊 `ADJACENT_PRIMARY_NATIVE_CONDENSATE_SUPPORT_PRESENT`，現在被更精確定義成 boundary-only。

## 測試
- Focused/integration：21/21 PASS。
- Working-tree full regression：571/571 PASS。
- FULL-CLEAN extracted regression：待 release gate 最後封裝完成後更新。

## 下一步
1. 完成 R5.7.41 FULL-CLEAN release gate。
2. 只跑一次 R5.7.41 完整線上 CASE，確認：
   - 新三份 overlap CSV；
   - `CANVAS_VERTICAL_MICROPHYSICS_OVERLAP` PASS；
   - R5.7.40.1 science CSV 無非預期變更；
   - CASE / Analysis Integrity PASS。
3. 再進 R5.7.42 GFS Native 127 Model-Level Provider Probe；不得直接下載整個 6GB `atmf*.nc`，先研究 subset/range/S3 可行性。
4. R5.7.43 才研究 COT/COD microphysics closure；assumed r_eff 只能稱 estimate，不得叫 exact/native COT。
