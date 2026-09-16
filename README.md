> Current release: **V1.0-R5.7.41.3.4.10.20** — Step 3G Primary Wyser Eq.(5)/(6) Numeric Recovery Audit + Synthetic Closure Harness Readiness; science baseline remains frozen at `R5.7.41.2_SHADOW_COT_AB_FROZEN`.

# Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.20


## R5.7.41.3.4.10.20 Step 3G — Primary Wyser Numeric Recovery Audit + Synthetic Closure Harness

- Wyser Eq.(5)/(6) primary semantic/units remain pinned, but machine-readable numeric equations are **not** promoted.
- `D=2.5L^0.6` remains corroborated non-primary lineage only.
- Corrupt Eq.(6) flat/OCR extraction is explicitly rejected as a coefficient source.
- A synthetic-only diagnostic mass-closure harness is ready; it can validate the normalization algorithm but can never set scientific mass closure PASS.
- Absolute PSD reconstruction, Wyser L→Yang/Bi Dmax, habit/roughness selection, bulk Ice tau and production promotion remain blocked.


## R5.7.41.3.4.10.19 Step 3F — Exact Wyser Eq.(5)/(6) Geometry + Mass-Size / PSD Mass-Closure Qualification

- Primary-source Wyser normalization rule is pinned: `n(L)=A·phi(L)` and `A=IWC/∫m(L)phi(L)dL`.
- Mixed PSD shape remains Gamma (≤20 µm) + power law (>20 µm), with continuity at 20 µm.
- This does **not** make numerical absolute PSD reconstruction executable: exact primary-quality `m(L)` / Eq.(6) and Eq.(5) column geometry remain unresolved.
- Later `D=0.7L / D=6.96√L` column relations are reference-only and may not substitute for Wyser Eq.(5).
- `Wyser L → Yang/Bi maximum_dimension_um` remains blocked until exact geometry is pinned and mass closure is validated.
- No Dmax synthesis, no habit/roughness default, no production Ice τ, and no Formation promotion.

## R5.7.41.3.4.10.17 Step 3D — Wyser PSD + Yang/Bi Habit Bulk-Integration Contract Qualification

- Mixed PSD core, 10–1000 µm nominal integration domain, GFS-v16 public B(T,IWC), Yang/Bi optical domain and six-band bulk integration mathematics were pinned.
- Absolute PSD normalization, exact column geometry, L→Dmax coordinate, habit/roughness and independent validation remained blocked.

## R5.7.41.3.4.10.16 Step 3C — GFS v16 Effective-Radius ↔ Yang/Bi Dmax Bridge Feasibility Audit

- `GFDL/Wyser rei` 被正式定義為 bulk effective-radius semantic；不得直接轉為 Yang/Bi `maximum_dimension_um`。
- 禁止 `Dmax=rei`、`Dmax=2×rei`、effective diameter 直接改名 Dmax，以及 `reimin/reimax` 當 Dmax bounds。
- 公開 GFDL parameter comment 與 v1/2019 實際 `reiflag=2` source branch 的算法標籤存在 mismatch；本版保存為 provenance blocker，不自行消除。
- 識別較合理的候選：重建 compatible Wyser PSD/hex-column population，再對 authoritative Yang/Bi Dmax single-particle optics 做 bulk integration。
- 此 bulk integration 目前仍 `IDENTIFIED_NOT_QUALIFIED`；habit、roughness、PSD/aspect-ratio、uncertainty、independent validation 未完成。
- Formation / Viewing / Twilight Glow / 六波段 / Frozen Science 全部不變。

## R5.7.41.3.4.10.15.1 Step 3B CASE Evidence Handoff Integrity Hotfix

- 修正 `.10.15` FIELD CASE 中 Step 3B evidence archive handoff 空檔問題。
- CASE export 由 release builder 重建 scheme-pin evidence，Archive Integrity 同時檢查內容非空。
- 不更動 Frozen Science。

## R5.7.41.3.4.10.15 Ice Optics Phase 2 Step 3B — GFS v16 Exact Scheme Pinning Evidence Gate

本版延續 `.10.13 FIELD PASS`，將「**全球可用**」正式設定為 Ice Microphysics mapping candidate 的優先資格。它只做來源／scheme qualification，不執行 Dmax/PSD mapping，也不改 Formation、Viewing、Twilight Glow 或 Production Ice Optics。

核心策略：
- **Priority 1：NOAA GFS v16 / GFDL Cloud Microphysics** — 全球、現行 operational、PhysicsCore 已使用 GFS native mass fields。只有在 exact operational scheme revision、namelist/config、PSD/mass-size relation 與 size semantic 都被釘死後，才允許進下一層 mapping validation。
- **Priority 2：NOAA GFS v17 / Thompson** — 2026-09-16 尚未 operational；NOAA 2026 公告提議 2026-10 升級。Thompson scheme 有 cloud-ice number concentration 與 explicit ice-distribution logic，但目前只能列 future global candidate。
- **Priority 3：DWD ICON global** — 全球 operational；全球公開資料目前有 ice mass，但不可假設 global grid 使用 double-moment qni contract。
- **Reference：GFDL SHiELD MPv3** — 有明確 gamma PSD 與 scheme-native mass→PSD 數學，可做 reconstruction methodology reference；不得直接假定等同 GFS v16 runtime。
- **Reference：ECMWF IFS effective dimension** — 是 radiation effective size，不是 Yang/Bi `maximum_dimension_um`。
- **NASA GEOS-FP** — 全球 mass state 可用，但目前公共 forecast state 不足以解鎖 size/PSD mapping。

新增 CASE 證據：
- `ice_microphysics_global_mapping_candidate_registry.csv`
- `ice_microphysics_global_mapping_qualification_gate.csv`
- `ice_microphysics_global_mapping_candidate_contract.json`

新增 Analysis Integrity gate：
- `ICE_MICROPHYSICS_GLOBAL_CANDIDATE_EVIDENCE_PRESENT`
- `ICE_MICROPHYSICS_GLOBAL_CANDIDATE_CONTRACT_FREEZE`
- `ICE_MICROPHYSICS_GLOBAL_CANDIDATE_FAIL_CLOSED`

禁止事項仍包括：跨版本套用 GFDL MPv3→GFSv16、在 GFSv17 operational 前提前使用 Thompson、把 ICON double-moment 假設到 global operational、把 effective radius/diameter 當 Dmax、mass-only 直接造 PSD、mass+number 未經 scheme contract 直接造 Dmax、固定 habit/roughness。

## Frozen Science

`R5.7.41.2_SHADOW_COT_AB_FROZEN` 不變。Formation / Viewing / Twilight Glow、六波段 550/575/600/650/700/750 nm、Canvas/Corridor/REZ、Earth Shadow、Production/Shadow COT、Missing ≠ Clear ≠ Zero、WINDY portable decoupling 均未修改。
