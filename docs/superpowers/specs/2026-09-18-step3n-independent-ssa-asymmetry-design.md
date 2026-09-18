# Step 3N Independent SSA + Asymmetry Qualification Design

## 目標
在 R5.7.41.3.4.10.26 FIELD PASS 之後，新增診斷限定的獨立 ice-cloud SSA / asymmetry cross-check，不修改 Frozen Science，不開啟 production ice optics。

## 科學定位
1. Yang/Bi V2 仍是被驗證的 authoritative ice-particle LUT。
2. 獨立 reference chain 使用 Fu (1996) solar cirrus parameterization 的外部實作證據；RRTMG/GFS/CCPP 將 `ssaice3` / `asyice3` 明確標示為 Fu(1996) ice-cloud coefficients。
3. Fu96/RRTMG reference 是 bulk-band parameterization，不是 Yang/Bi `single_column + roughness` 的逐粒子同幾何 reference。
4. RRTMG visible shortwave bands 24/25 是寬頻。550/575/600 nm 落在 band 25，650/700/750 nm 落在 band 24；不得把寬頻 reference 偽裝成六個獨立單色 authoritative values。
5. 因此 Step 3N 可執行 independent bulk-band SSA/g cross-check；但 `full_six_band_like_for_like_optical_validation_pass` 必須維持 false。

## Fail-close 規則
- `independent_bulk_band_ssa_reference_available` 可因 Fu96/RRTMG provenance 通過。
- `independent_bulk_band_asymmetry_reference_available` 可因 Fu96/RRTMG provenance 通過。
- 未完成可重現數值比較前，`independent_ssa_validation_pass=false`、`independent_asymmetry_validation_pass=false`。
- 即使 bulk-band 數值比較完成，也不得自動將其等價於六波段單色驗證。
- `full_like_for_like_optical_validation_pass=false`。
- `tau_ice_production_allowed=false`。
- `production_ice_optics_ready=false`。
- `physics_promotion_allowed=false`。
- 不修改 Formation / Viewing / Twilight Glow。
- 不推導 GFS native habit / roughness truth。

## Artifacts
- `ICE_MICROPHYSICS_FU96_RRTMG_SSA_ASYMMETRY_QUALIFICATION_EVIDENCE_R5.7.41.3.4.10.27.csv`
- `ICE_MICROPHYSICS_FU96_RRTMG_SSA_ASYMMETRY_QUALIFICATION_GATE_R5.7.41.3.4.10.27.csv`
- `ICE_MICROPHYSICS_FU96_RRTMG_SSA_ASYMMETRY_QUALIFICATION_CONTRACT_R5.7.41.3.4.10.27.json`
- CASE archive 同步保存上述三件 artifacts，並加入 analysis/archive integrity checks。

## Acceptance
- evidence / gate / contract deterministic serialization。
- CASE handoff 完整。
- 舊 Step 3M extinction gate 不退化。
- Frozen Science 與 production fail-close 全部維持。
- working-tree full regression、candidate fresh-extract full regression、final immutable full regression 全綠後，狀態只能是 `QA PASS / FIELD VALIDATION PENDING`。
