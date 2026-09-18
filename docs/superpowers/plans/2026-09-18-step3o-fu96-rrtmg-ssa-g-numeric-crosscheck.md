# Step 3O Fu96/RRTMG SSA + Asymmetry Numeric Cross-Check Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立可重現、fail-close 的 Fu96/RRTMG broad-band SSA/g 數值 cross-check，版本升至 R5.7.41.3.4.10.28。

**Architecture:** 以 pinned RRTMG band 24/25 table 為獨立 reference；由現有 Wyser PSD + Yang/Bi single-column geometry/optics計算 population Dge 與六波段 bulk SSA/g，再以 band-local sample mean/range做 diagnostic comparison。數值流程可通過，但 spectral non-equivalence 持續阻擋正式 SSA/g validation 與 production promotion。

**Tech Stack:** Python 3、NumPy、pandas、pytest、既有 PhysicsCore ice microphysics modules。

**Spec:** `docs/superpowers/specs/2026-09-18-step3o-fu96-rrtmg-ssa-g-numeric-crosscheck-design.md`

## Global Constraints

- Science baseline 固定 `R5.7.41.2_SHADOW_COT_AB_FROZEN`。
- 六波段維持 550/575/600/650/700/750 nm。
- 不修改 Formation / Viewing / Twilight Glow。
- 不允許 runtime habit/roughness inference。
- 不允許 `tau_ice` production、Production Ice Optics、physics promotion。
- 不新增 science tolerance。

---

### Task 1: Pinned RRTMG visible reference

**Files:**
- Create: `firecloud/data/ice_optics/fu96_rrtmg_visible_band24_25_reference_v1.csv`
- Test: `tests/test_r5741341028_fu96_rrtmg_ssa_asymmetry_numeric_crosscheck.py`

**Interfaces:**
- Produces: 46 `dge` nodes for each of RRTMG bands 24/25 with `ssa`, `g`, `ext` and pinned provenance.

- [ ] Write failing test for row count, node grid, physical bounds and provenance.
- [ ] Run test and verify RED.
- [ ] Add exact pinned source values.
- [ ] Run test and verify GREEN.

### Task 2: Numeric cross-check core

**Files:**
- Create: `firecloud/ice_microphysics_fu96_rrtmg_ssa_asymmetry_numeric_crosscheck.py`
- Test: `tests/test_r5741341028_fu96_rrtmg_ssa_asymmetry_numeric_crosscheck.py`

**Interfaces:**
- Produces: `run_fu96_rrtmg_ssa_asymmetry_numeric_crosscheck_grid()`, `build_..._evidence()`, `build_..._gate()`, `..._contract_payload()`.

- [ ] Write failing tests for 54 rows, Dge domain, deterministic results and fail-close gates.
- [ ] Run and verify RED.
- [ ] Implement Dge bridge, Yang bulk SSA/g weighting, RRTMG interpolation, summary characterization.
- [ ] Run and verify GREEN.

### Task 3: CASE handoff

**Files:**
- Modify: `firecloud/model.py`
- Modify: `app.py`
- Modify: `firecloud/case_integrity.py`
- Test: `tests/test_r5741341028_fu96_rrtmg_ssa_asymmetry_numeric_crosscheck_handoff.py`

**Interfaces:**
- CASE members: `ice_microphysics_fu96_rrtmg_ssa_asymmetry_numeric_crosscheck_evidence.csv`, `..._gate.csv`, `..._contract.json`.

- [ ] Write handoff/integrity RED tests.
- [ ] Wire analysis result, export and integrity checks.
- [ ] Verify GREEN without weakening archive gates.

### Task 4: Release identity and artifacts

**Files:**
- Modify: `firecloud/__init__.py`, `app.py`, current-version tests/README.
- Create: `.10.28` CURRENT_PROJECT_STATE / IMPLEMENTATION_STATUS / RELEASE_NOTES / TEST_REPORT / 中文使用者版更新說明。

- [ ] Write release identity RED test.
- [ ] Upgrade current identity to `1.0.0-R5.7.41.3.4.10.28` and Step 3O.
- [ ] Generate deterministic Step 3O evidence/gate/contract artifacts.
- [ ] Run focused Step 3N/3O/UI regression.

### Task 5: Release closure

- [ ] Run collect-only and full working-tree regression.
- [ ] Build candidate FULL-CLEAN with zero cache/pyc.
- [ ] Fresh-extract full regression.
- [ ] Regenerate Step 3O artifacts and byte-compare.
- [ ] Write candidate results into release docs and rebuild immutable final ZIP.
- [ ] Final read-only full regression, artifact byte-exact, ZIP CRC and SHA256.
