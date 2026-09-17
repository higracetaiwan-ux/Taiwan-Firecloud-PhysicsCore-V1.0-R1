# CURRENT PROJECT STATE — Taiwan Firecloud PhysicsCore V1.0

## Current Version

`V1.0-R5.7.41.3.4.10.23.1`

Status: **QA PASS — FIELD VALIDATION PENDING**

Science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`

Latest formal FIELD baseline: `V1.0-R5.7.41.3.4.10.22 FIELD PASS`

`.10.23` status: **FIELD SCIENCE PASS / archive telemetry hotfix required**（TWS091 + TWS100, 2026-09-17 sunrise）。

## Current Milestone

Step 3J.1 — **CAMS Terminal Checkpoint Reconciliation + Stable Diagnostic Evidence Serialization**

## Hotfix result

- child `TIMEOUT_DEFERRED` durable checkpoint reconciliation：PASS
- terminal role/PID/exit/error/path provenance preservation：PASS
- Step 3J evidence float serialization fixed at 16 significant digits：PASS
- 1-ULP pair `35.736078690506133` / `35.736078690506126` → `35.73607869050613`：PASS
- Step 3J science equations / raw values：UNCHANGED
- Frozen Science：UNCHANGED

## Step 3J gate

`DIAGNOSTIC_BETA_KEXT_NUMERIC_READY_SCIENTIFIC_AND_TAU_PROMOTION_BLOCKED`

### Passed

- diagnostic six-band β_ext / k_ext numeric integration
- PSD numeric mass closure
- bulk-grid convergence
- stable release evidence serialization

### Still blocked

- independent exact numeric corroboration for Wyser Eq.(6)
- scientific bulk-optics validation
- Yang/Bi habit bridge
- Yang/Bi roughness bridge
- bulk production eligibility
- `tau_ice` production synthesis
- GFSv16 Dmax runtime mapping
- Production Ice Optics
- `physics_promotion_allowed=false`

## QA

Working-tree full regression: **874/874 PASS** (1 existing pandas FutureWarning).

Candidate FULL-CLEAN fresh-extract regression: **874/874 PASS** (1 existing pandas FutureWarning).

Step 3J evidence/gate/contract deterministic regeneration: **byte-exact PASS**.

## Next Step

以 `.10.23.1` 重跑 **TWS100 / 2026-09-17 sunrise**，優先驗證 pressure-level bundle 再次走 `TIMEOUT_DEFERRED` 時 checkpoint 會正確 terminalize；若當次 CAMS 沒有 timeout，CASE 仍可驗證一般路徑，但 timeout-path FIELD closure 需等待下一個實際 timeout case。
