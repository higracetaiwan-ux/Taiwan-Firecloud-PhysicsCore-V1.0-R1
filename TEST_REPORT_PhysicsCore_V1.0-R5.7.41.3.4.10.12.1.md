# Test Report — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.12.1

## Targeted regression
29 passed / 0 failed

涵蓋：
- `.10.12.1` Phase 2 Evidence Integrity Gate
- `.10.12` Native Microphysics Capability Audit
- `.10.10` Ice Cloud Spectral Optics Shared
- `.10.10.1` WINDY portable decoupling

## Full regression
**776 passed / 0 failed / 1 warning**

Warning 為既有 pandas DataFrame concat FutureWarning，位置 `tests/test_r5732_glow_observer_aerosol_coverage.py`，非本版功能失敗。

## 新增 gate 驗證
- Phase 2 evidence 三件套存在 → PASS。
- contract 缺失 → `ICE_MICROPHYSICS_PHASE2_EVIDENCE_PRESENT` FAIL。
- Dmax/PSD/habit/roughness readiness 未成立 → 必須維持 fail-closed。
- Archive manifest 缺任何一個 Phase 2 artifact → 對應 `ARCHIVE_MEMBER::*` FAIL。

## 科學回歸
Frozen science baseline `R5.7.41.2_SHADOW_COT_AB_FROZEN` 未改動。
