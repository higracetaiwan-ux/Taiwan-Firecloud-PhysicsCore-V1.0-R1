# Step 3P Full-Spectral Source Qualification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic fail-closed qualification for Yang/Bi V2 full-spectrum source availability and RRTMG band 24/25 spectral-domain coverage.

**Architecture:** A focused qualification module consumes the existing authoritative source contract and optional source-root path. It emits evidence, a one-row gate and canonical JSON contract; model/app/case-integrity handoff follows the Step 3O pattern without enabling any optical production path.

**Tech Stack:** Python, pandas, numpy, pytest.

**Spec:** `docs/superpowers/specs/2026-09-18-step3p-full-spectral-source-qualification-design.md`

## Global Constraints
- Frozen science baseline stays `R5.7.41.2_SHADOW_COT_AB_FROZEN`.
- Never synthesize a 396-wave spectrum from six portable wavelengths.
- Exact Fu96/RRTMG band weighting remains false unless independently proven.
- All SSA/g validation and production gates remain false.

---

### Task 1: Step 3P qualification core
**Files:**
- Create: `firecloud/ice_microphysics_yang_full_spectral_source_qualification.py`
- Test: `tests/test_r5741341029_yang_full_spectral_source_qualification.py`

**Interfaces:**
- Produces `build_yang_full_spectral_source_qualification_evidence(source_root=None)`, `build_yang_full_spectral_source_qualification_gate(evidence)`, `yang_full_spectral_source_qualification_contract_payload(...)`, and canonical serializer.

- [ ] Write failing tests for absent source, band-domain coverage helper, fail-close gate and stable serialization.
- [ ] Run the focused test and confirm RED.
- [ ] Implement the smallest qualification module.
- [ ] Run focused tests and confirm GREEN.

### Task 2: CASE/model/integrity handoff
**Files:**
- Modify: `firecloud/model.py`
- Modify: `app.py`
- Modify: `firecloud/case_integrity.py`
- Test: `tests/test_r5741341029_yang_full_spectral_source_qualification_handoff.py`

**Interfaces:**
- Adds analysis-result keys and CASE members for Step 3P evidence/gate/contract.

- [ ] Write failing handoff tests.
- [ ] Confirm RED.
- [ ] Add model/app/archive-integrity handoff using canonical contract serialization.
- [ ] Confirm GREEN.

### Task 3: Release identity and closure
**Files:**
- Modify: `firecloud/__init__.py`
- Modify: `README.md`
- Create versioned Step 3P artifacts and Traditional-Chinese release documents.

- [ ] Add release-identity test for `.10.29` and confirm RED.
- [ ] Update current version identity and milestone text.
- [ ] Run focused and full regression.
- [ ] Build candidate FULL-CLEAN, fresh-extract test, regenerate Step 3P artifacts byte-exact.
- [ ] Build final immutable FULL-CLEAN and repeat read-only verification before QA closure.
