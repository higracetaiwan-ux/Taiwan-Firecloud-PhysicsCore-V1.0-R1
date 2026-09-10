# Taiwan Firecloud PhysicsCore — Current Project State V1.0-R5.7.37

## 現行版本

**V1.0-R5.7.37 — Near-Surface Molecular Boundary Closure**

## 本版目的

補足 Twilight Glow `Scatter→Observer` 近地分子路徑在 ML137 與最低 pressure-level 之間的真實垂直資料空間，同時保留原有 10 m endpoint tolerance，不以放寬 tolerance 取得假完整率。

## 凍結規則保持

- 太陽角度：0° 至 −6°，0.5° 間隔，共 13 點。
- 六波段：550/575/600/650/700/750 nm。
- Formation / Viewing / Twilight Glow 三軌永久分離。
- Primary Canvas 0–40 km；Extended Canvas 40–100 km。
- `<2 km` 低雲不作 Formation Canvas，但仍保留 blocker/view obstruction。
- Missing ≠ Clear ≠ Zero ≠ N/A。
- molecular lowest endpoint tolerance：**0.01 km（10 m）固定**。

## 已關閉版本

- R5.7.35：Aerosol Scattering Physics Phase 1，FIELD PASS。
- R5.7.35.1：Aerosol Missing-Reason Handoff，FIELD PASS。
- R5.7.35.2：Zero-Eligible Viewing Precipitation Integrity Semantics，CODE/REGRESSION CLOSED。
- R5.7.36：Formation Canvas Eligibility / Low-Cloud Role Separation，CODE/REGRESSION CLOSED；日本 0–100 km 低雲 fresh CASE 仍建議補做 field-close。

## R5.7.37 狀態

- Code：CLOSED
- Regression：CLOSED；working tree **533/533 PASS**，FULL-CLEAN 解壓後 **533/533 PASS**。
- FULL-CLEAN 封包：CLOSED；**506 個檔案成員，0 cache/pyc 污染**。
- Field Validation：OPEN

## 下一個 field validation 必查

1. `cams_request_audit.csv` 是否有 `O3_NEAR_SURFACE_MODEL_LEVEL_137`，且每個 required time slice 成功。
2. `gas_profile_route_snapshots.csv` 是否出現 `near_surface_boundary_state=READY`。
3. ML137 anchor 高度、pressure、O₃ provenance 是否合理。
4. `NEAR_SURFACE_MOLECULAR_BOUNDARY_FROZEN_10M_TOLERANCE = PASS`。
5. 台灣既有 100 km / 3.75 km molecular rows 是否成為 156/156 resolved。
6. 若 provider evidence Missing，是否仍正確 Partial/Missing，沒有 false closure。

## 後續主線

R5.7.37 field validation 後，下一個 operational reliability 項目為 CAMS Post-success Download Recovery（針對日本 CASE 曾出現的 successful remote job 後 502 + 120 秒 download retry）。
