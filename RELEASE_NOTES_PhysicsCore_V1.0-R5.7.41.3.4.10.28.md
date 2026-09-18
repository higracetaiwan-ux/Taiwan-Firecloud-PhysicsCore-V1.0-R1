# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.28

## Step 3O — Fu96/RRTMG SSA + Asymmetry Numeric Cross-Check

本版把 `.10.27` 已固定的 Fu96/RRTMG broad-band SSA/g reference 推進到可重現的 numeric cross-check。

### 新增

- `firecloud/data/ice_optics/fu96_rrtmg_visible_band24_25_reference_v1.csv`
  - 92 records；RRTMG visible bands 24/25；46 個 Dge nodes / band。
- `firecloud/ice_microphysics_fu96_rrtmg_ssa_asymmetry_numeric_crosscheck.py`
  - Wyser population → Yang/Bi bulk SSA/g。
  - `Dge = 4/(3√3) × De_bulk` diagnostic bridge。
  - Fu96/RRTMG broad-band interpolation。
  - 54-row numeric comparison matrix。
- Step 3O evidence / gate / contract 與 CASE integrity handoff。

### 科學邊界

RRTMG 是 broad-band reference；目前 Yang/Bi portable LUT 只有六個 monochromatic samples。兩者 spectral semantics 不等價，因此本版只宣告 `NUMERIC_CROSSCHECK_EXECUTED_PASS=true`，不宣告 SSA/g scientific validation PASS。

### 不變

Frozen Science、Formation / Viewing / Twilight Glow、runtime habit/roughness policy、`tau_ice` production、Production Ice Optics 全部不變。
