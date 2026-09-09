# Taiwan Firecloud PhysicsCore V1.0-R5.7.29.1 Release Notes

## Field CASE forensic

CASE：`Taiwan-Firecloud-PhysicsCore-V1.0-R5.7.29_2026-09-09_sunset_CASE.zip`

- CASE archive 與原版 Analysis/CASE Integrity 均顯示 PASS。
- GFS inventory/completeness 證明 RWMR、SNMR、GRLE 各有 22 pressure levels，
  狀態為 READY。
- eligible Viewing targets 為 110，但 Viewing precipitation evidence 為 0 rows。
- 77 targets 為 `VIEW_PARTIAL_SIX_BAND_RT`，33 local targets 為 unresolved；Full
  completeness 為 0%。
- 根因是 `AngleFrameSpool.cleanup()` 早於 `viewing_route_snapshot` drain。

原 CASE 保持 immutable，不回寫其 CSV 或 Integrity 結果。

## Hotfix

- cleanup 移至 Viewing snapshot drain 後。
- `v1_viewing_precipitation_evidence` 加入 pre-export Integrity handoff。
- 新增 `VIEWING_PRECIPITATION_TARGET_COVERAGE`。
- 新增 `VIEWING_NATIVE_HYDROMETEOR_HANDOFF`。
- 原 R5.7.29 CASE 在新規則下會正確揭露 `expected=110; observed=0` 與 native
  hydrometeor handoff FAIL。

## Verification

- R5.7.29.1 targeted regression：27 passed / 0 failed。
- Working tree full regression：474 passed / 0 failed。
- FULL-CLEAN extraction regression：474 passed / 0 failed。

真實 precipitation rows 與 Full RT 必須由 R5.7.29.1 新部署 CASE 驗證；本版不以
舊 CASE 或 synthetic values 冒充 field PASS。
