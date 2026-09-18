# Step 3O Fu96/RRTMG SSA + Asymmetry Numeric Cross-Check Design

## Goal

在不改動 Frozen Science、Formation / Viewing / Twilight Glow、runtime habit/roughness、`tau_ice` production 的前提下，將 Step 3N 已固定的 Fu96/RRTMG broad-band SSA/g reference 從「來源可用」推進到可重現的數值 cross-check。

## Scientific boundary

1. RRTMG `ICEFLAG=3` 的 Fu96 `ssaice3` / `asyice3` 是 broad-band bulk parameterization，不是 550/575/600/650/700/750 nm monochromatic truth。
2. 使用 pinned RRTMG band 24/25、46-node `dge=5,8,...,140 µm` table；不得外插。
3. Yang/Bi 端維持 `single_column` + Rough000/Rough003/Rough050，並以 Wyser PSD 做 population weighting。
4. Yang bulk effective diameter依 `De = (3/2) * integral(V n dD) / integral(A n dD)`；Fu generalized effective size bridge採 `Dge = 4/(3*sqrt(3)) * De`。此 bridge 是 diagnostic qualification hypothesis，不是 runtime truth。
5. Yang/Bi 六個單色點只能形成 band 25 的 550/575/600 sample 與 band 24 的 650/700/750 sample；沒有完整 band spectral weighting，因此只計算 sample mean/range 與 RRTMG broad-band reference 的差異。
6. 本步可標記 `NUMERIC_CROSSCHECK_EXECUTED_PASS=true`（代表數值流程完整、finite、in-domain、deterministic），但 `INDEPENDENT_SSA_VALIDATION_PASS=false`、`INDEPENDENT_ASYMMETRY_VALIDATION_PASS=false`、`FULL_SIX_BAND_LIKE_FOR_LIKE_OPTICAL_VALIDATION_PASS=false`。
7. 不建立新的科學 tolerance；輸出的 SSA/g 差值僅為 regression characterization。

## Outputs

- `firecloud/data/ice_optics/fu96_rrtmg_visible_band24_25_reference_v1.csv`
- `firecloud/ice_microphysics_fu96_rrtmg_ssa_asymmetry_numeric_crosscheck.py`
- Step 3O evidence CSV / gate CSV / contract JSON
- analysis result、CASE archive、case integrity handoff

## Acceptance

- 27 population states = 3 temperatures × 3 IWC × 3 roughness；2 RRTMG visible bands => 54 comparison rows。
- 所有 derived `dge` 必須在 5–140 µm 內；禁止外插。
- 所有 Yang bulk SSA/g 與 Fu96/RRTMG interpolated SSA/g 必須 finite 且 physical-domain valid。
- evidence/gate/contract deterministic serialization。
- production gates全部保持 false。
- full regression、fresh-extract regression、artifact byte-exact regeneration 全部通過後，版本狀態才可為 QA PASS / FIELD VALIDATION PENDING。
