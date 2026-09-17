# IMPLEMENTATION STATUS — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.23

## Status

**QA PASS — FIELD VALIDATION PENDING**

Latest FIELD baseline：`V1.0-R5.7.41.3.4.10.22 FIELD PASS`。

## Step 3J implemented

- 新增 `firecloud/ice_microphysics_wyser_yang_diagnostic_bulk_integration.py`。
- 以 Wyser Eq.(6) normalized PSD 作 number population。
- 以 Step 3I Yang/Bi V2 `single_column/Rough000` diagnostic `C_ext(Dmax,λ)` 作 optical kernel。
- 六波段計算 `β_ext`、`k_ext`。
- source-knot-preserving log-log interpolation，禁止 extrapolation。
- 18-case numerical matrix + mass closure + grid convergence。
- Step 3J evidence/gate/contract 接入 model、Analysis Integrity、CASE archive required members/content gates。

## Fail-close preserved

- 不計算 production `tau_ice`。
- 不選 runtime habit / roughness。
- 不寫 Step 3J `k_ext` 到 ice runtime。
- 不允許 `BULK_YANG_BI_PSD_INTEGRATION_ELIGIBLE`。
- 不允許 `PRODUCTION_ICE_OPTICS_READY`。
- 不允許 `physics_promotion_allowed`。
- Frozen Formation / Viewing / Twilight Glow 不變。
