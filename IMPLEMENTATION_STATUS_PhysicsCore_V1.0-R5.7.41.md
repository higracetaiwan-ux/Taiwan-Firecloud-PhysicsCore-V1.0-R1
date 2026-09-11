# Implementation Status — PhysicsCore V1.0-R5.7.41

## 已完成
- [x] `firecloud/canvas_vertical_microphysics_overlap.py`
- [x] pgrb2 + pgrb2b merged direct-native vertical samples
- [x] target Cloud Base–Top position classification
- [x] boundary-only vs strict-interior support
- [x] expected pgrb2b level Missing preservation
- [x] bracket / coverage / max-gap diagnostics
- [x] assumed-r_eff COT diagnostic scaffold
- [x] conflict → COT diagnostic fail-close
- [x] no-promotion contract
- [x] model pipeline handoff
- [x] Analysis Integrity guard
- [x] CASE CSV export
- [x] offline CASE replay tool
- [x] 21/21 focused/integration PASS
- [x] 571/571 working-tree full regression PASS

## 尚未做（刻意不混入本版）
- [ ] GFS 127 model-level `atmf*.nc` provider
- [ ] native model-level remote subset / range access
- [ ] true COT/COD microphysics closure
- [ ] effective-radius native source closure
- [ ] COT / Formation promotion contract
- [ ] multiple scattering / absolute radiometric calibration

## Field 狀態
R5.7.41 production online Field Validation：**尚未執行**。

開發階段已使用 2026-09-11 sunset CASE -2 做無網路 semantic replay；最後只需要一次完整線上 CASE 驗證新 CSV / Integrity 與 science non-regression。
