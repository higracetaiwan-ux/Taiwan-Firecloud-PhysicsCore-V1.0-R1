> Current release: **V1.0-R5.7.41.3.4.10.14** — Ice Optics Phase 2 Step 3: Global Mapping Candidate Intake + Scheme Contract Qualification; science baseline remains frozen at `R5.7.41.2_SHADOW_COT_AB_FROZEN`.

# Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.14

## R5.7.41.3.4.10.14 Ice Optics Phase 2 Step 3 — Global Mapping Candidate Intake + Scheme Contract Qualification

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
