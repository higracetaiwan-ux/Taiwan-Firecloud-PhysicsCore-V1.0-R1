# Step 3I Wyser ↔ Yang/Bi Population Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Add a diagnostic-only, fail-closed Wyser population ↔ Yang/Bi optical-kernel bridge on the qualified Dmax coordinate.

**Architecture:** Keep Step 3H immutable and add a new Step 3I module. Separate Wyser Eq.(6) population mass from Yang `rho*V` optical-kernel mass, reconstruct Yang single-particle Cext from the portable LUT, quantify geometry/mass non-equivalence, and archive independent Step 3I evidence/gate/contract.

**Tech Stack:** Python, pandas, numpy, pytest, Streamlit app export, existing PhysicsCore CASE integrity framework.

**Spec:** `docs/superpowers/specs/2026-09-17-step3i-wyser-yang-population-bridge-design.md`

## Global Constraints
- Science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`.
- Version target: `1.0.0-R5.7.41.3.4.10.22`.
- Six bands: 550/575/600/650/700/750 nm.
- Wyser PSD domain: 10–1000 µm.
- No production ice-optics promotion in Step 3I.
- Missing ≠ Clear ≠ Zero.

---

### Task 1: Core population/kernel diagnostic

**Files:**
- Create: `firecloud/ice_microphysics_wyser_yang_population_bridge.py`
- Test: `tests/test_r5741341022_wyser_yang_population_bridge.py`

**Interfaces:**
- Consumes: Step 3G `wyser_eq5_width_um`, `wyser_eq6_mass_g`; Step 3H Yang column geometry; shared `ICE_DENSITY_KG_M3` and bundled LUT.
- Produces: geometry diagnostic, Yang Cext kernel reconstruction diagnostic, combined Step 3I population-bridge diagnostic.

- [x] Write tests requiring dual-mass separation, 109 Dmax sizes / 654 six-band Rough000 kernel rows in the 10–1000 µm overlap, finite positive reconstructed Cext/Qext, and explicit non-equivalence of Wyser/Yang area/volume/mass.
- [x] Run focused tests and verify RED because the Step 3I module does not exist.
- [x] Implement the minimal diagnostic module.
- [x] Run focused tests and verify GREEN.

### Task 2: Evidence, gate and contract

**Files:**
- Modify: `firecloud/ice_microphysics_wyser_yang_population_bridge.py`
- Test: `tests/test_r5741341022_wyser_yang_population_bridge.py`

**Interfaces:**
- Produces: `build_wyser_yang_population_bridge_evidence`, `build_wyser_yang_population_bridge_gate`, `wyser_yang_population_bridge_contract_payload`.

- [x] Add RED tests that allow only diagnostic kernel/dual-mass/numeric-executable gates to pass while all scientific/production gates remain false.
- [x] Implement evidence/gate/contract with portable provenance paths and forbidden-shortcut list.
- [x] Verify focused GREEN.

### Task 3: Model, integrity and CASE archive handoff

**Files:**
- Modify: `firecloud/model.py`
- Modify: `firecloud/case_integrity.py`
- Modify: `app.py`
- Test: `tests/test_r5741341022_wyser_yang_population_bridge_handoff.py`
- Modify: relevant CASE-required-member regression expectations.

**Interfaces:**
- Adds model keys for Step 3I evidence/gate/contract and required flag.
- Adds Analysis Integrity contract/fail-close checks and archive content requirements.

- [x] Write handoff tests first and verify RED.
- [x] Wire model/integrity/app export.
- [x] Verify Step 3I handoff tests GREEN.

### Task 4: Release identity, docs and static artifacts

**Files:**
- Modify: `firecloud/__init__.py`
- Modify: `app.py`
- Modify: `README.md`
- Create: `CURRENT_PROJECT_STATE_PhysicsCore_V1.0-R5.7.41.3.4.10.22.md`
- Create: `IMPLEMENTATION_STATUS_PhysicsCore_V1.0-R5.7.41.3.4.10.22.md`
- Create: `RELEASE_NOTES_PhysicsCore_V1.0-R5.7.41.3.4.10.22.md`
- Create: `TEST_REPORT_PhysicsCore_V1.0-R5.7.41.3.4.10.22.md`
- Create: `R5.7.41.3.4.10.22_中文使用者版更新說明.md`
- Create generated Step 3I evidence/gate/contract artifacts.

- [x] Update version/milestone regression expectations.
- [x] Generate deterministic evidence/gate/contract files.
- [x] Document `.10.21 FIELD PASS` as previous baseline and `.10.22 QA PASS / FIELD VALIDATION PENDING`.

### Task 5: Verification and FULL-CLEAN package

**Files:**
- Package: `Taiwan-Firecloud-PhysicsCore-V1.0-R5.7.41.3.4.10.22-FULL-CLEAN.zip`
- Package hash: matching `.sha256`

- [x] Run focused Step 3G–3I tests.
- [x] Run full pytest regression.
- [x] Build a cache-free FULL-CLEAN ZIP.
- [x] Fresh-extract the ZIP and rerun full pytest.
- [x] Regenerate Step 3I evidence/gate/contract from fresh extract and require exact match.
- [x] Compute SHA256 and report QA status without claiming FIELD PASS.
