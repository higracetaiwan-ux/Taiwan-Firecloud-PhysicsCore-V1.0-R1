# Step 3N Independent SSA + Asymmetry Qualification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立 R5.7.41.3.4.10.27 Step 3N Fu96/RRTMG independent bulk-band SSA/asymmetry qualification，同時維持 six-band exact validation 與 production optics fail-close。

**Architecture:** 新增獨立 Step 3N qualification module，輸出 evidence/gate/contract；model/app/case_integrity 只負責 handoff。Reference provenance 與 band mapping 明確分離，任何 bulk-band cross-check 都不得提升為 six-band exact like-for-like validation。

**Tech Stack:** Python 3, pandas, numpy, pytest, existing PhysicsCore CASE archive/integrity pipeline.

**Spec:** `docs/superpowers/specs/2026-09-18-step3n-independent-ssa-asymmetry-design.md`

## Global Constraints
- Science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`。
- 六波段 production contract 仍為 550/575/600/650/700/750 nm。
- Missing ≠ Clear ≠ Zero。
- Formation / Viewing / Twilight Glow 不變。
- 不得建立 runtime habit/roughness default。
- 不得建立 production `tau_ice` 或 production SSA/g。
- Step 3N 只允許 diagnostic / qualification output。

---

### Task 1: Step 3N core contract and fail-close gate

**Files:**
- Create: `firecloud/ice_microphysics_fu96_rrtmg_ssa_asymmetry_qualification.py`
- Test: `tests/test_r5741341027_fu96_rrtmg_ssa_asymmetry_qualification.py`

**Interfaces:**
- Produces: `build_fu96_rrtmg_ssa_asymmetry_qualification_evidence() -> pd.DataFrame`
- Produces: `build_fu96_rrtmg_ssa_asymmetry_qualification_gate(evidence: pd.DataFrame) -> pd.DataFrame`
- Produces: `fu96_rrtmg_ssa_asymmetry_qualification_contract_payload(physicscore_version: str) -> dict`

- [ ] Write RED tests asserting provenance, visible band mapping, deterministic artifact schema, and all production/full-like-for-like gates false.
- [ ] Run focused tests and confirm RED because module is absent.
- [ ] Implement minimal qualification module.
- [ ] Run focused tests and confirm GREEN.

### Task 2: CASE/model/app handoff

**Files:**
- Modify: `firecloud/model.py`
- Modify: `app.py`
- Modify: `firecloud/case_integrity.py`
- Test: `tests/test_r5741341027_fu96_rrtmg_ssa_asymmetry_qualification_handoff.py`

**Interfaces:**
- Result keys: `v1_ice_microphysics_fu96_rrtmg_ssa_asymmetry_qualification_evidence`, `v1_ice_microphysics_fu96_rrtmg_ssa_asymmetry_qualification_gate`, `ice_microphysics_fu96_rrtmg_ssa_asymmetry_qualification_contract`.
- Archive members mirror release artifact names.

- [ ] Write RED handoff tests for model keys, app archive members, analysis integrity, archive integrity.
- [ ] Run focused tests and confirm RED.
- [ ] Add minimal wiring, preserving all existing integrity strictness.
- [ ] Run focused handoff tests and confirm GREEN.

### Task 3: Version identity and release artifacts

**Files:**
- Modify: `firecloud/__init__.py`
- Modify: `README.md`
- Create release evidence/gate/contract and Traditional-Chinese release docs.
- Update only current-version assertions in tests.

- [ ] Write RED version assertion for `1.0.0-R5.7.41.3.4.10.27`.
- [ ] Confirm RED on `.10.26` identity.
- [ ] Update version and current milestone text.
- [ ] Generate deterministic Step 3N artifacts.
- [ ] Run Step 3M + Step 3N + UI/version focused tests.

### Task 4: Regression and immutable release closure

**Files:**
- Create: `CURRENT_PROJECT_STATE_PhysicsCore_V1.0-R5.7.41.3.4.10.27.md`
- Create: `IMPLEMENTATION_STATUS_PhysicsCore_V1.0-R5.7.41.3.4.10.27.md`
- Create: `RELEASE_NOTES_PhysicsCore_V1.0-R5.7.41.3.4.10.27.md`
- Create: `TEST_REPORT_PhysicsCore_V1.0-R5.7.41.3.4.10.27.md`
- Create: `R5.7.41.3.4.10.27_中文使用者版更新說明.md`

- [ ] Run full working-tree pytest.
- [ ] Build candidate FULL-CLEAN without cache/pyc.
- [ ] Fresh-extract candidate and run full pytest.
- [ ] Regenerate Step 3N artifacts and byte-compare.
- [ ] Write candidate verification into release docs, rebuild final immutable ZIP.
- [ ] Fresh-extract final ZIP, rerun full pytest, byte-compare artifacts, verify ZIP hygiene and SHA256.
- [ ] Final status remains `QA PASS / FIELD VALIDATION PENDING` until an actual `.10.27` FIELD CASE is supplied.
