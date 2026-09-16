# Test Report — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.12

## Working tree full regression

`pytest -q`

- **772 passed**
- **0 failed**
- **1 warning**
- warning 為既有 pandas `FutureWarning`，不是 `.10.12` 新增 failure。

## Phase 2 targeted regression

執行：

- `tests/test_r5741341012_ice_microphysics_capability_audit.py`
- `tests/test_r5741341010_ice_cloud_spectral_optics_shared.py`
- `tests/test_r57413410101_ice_optics_portable_decoupling.py`

結果：**25 passed / 0 failed**。

## `.10.12` 新增 gates

1. `ICMR + positive IWP + temperature + RH + cloud fraction` 不得自動產生 Dmax。
2. `ice_effective_radius_um` 即使有值，也不得 substitute Dmax。
3. Positive IWP + missing Dmax 仍為 `ICE_MAXIMUM_DIMENSION_MISSING`。
4. IWP audit 必須標記為 `DETERMINISTIC_DERIVED`，不可標成 GFS native。
5. Dmax / r_eff / habit / roughness runtime slot 與 native provider capability 必須分離。
6. 沒有 native PSD size bins / number concentration / moments 時，狀態必須是 `INSUFFICIENT_PSD_INPUTS`。
7. habit 與 roughness 不可 default-fill。
8. `physics_promotion_allowed=false`。
9. CASE wiring 必須包含兩份 Phase 2 CSV 與 contract JSON。

## Real CASE replay

來源：`.10.11.2 TWS175 2026-09-17 sunrise FIELD PASS CASE`

Replay：

- 408 GFS inventory rows
- 96,876 native voxel rows
- 2,691 native cloud column rows
- 2,691 Ice runtime rows
- 213 positive-IWP rows
- 0 Dmax rows
- 0 r_eff rows
- 0 resolved habit rows
- 0 resolved roughness rows

Expected / actual：

`INSUFFICIENT_MICROPHYSICS` — **PASS**

## Science boundary

- `R5.7.41.2_SHADOW_COT_AB_FROZEN` unchanged.
- Formation / Viewing / Twilight Glow / Production COT unchanged.
- No new Dmax, PSD, habit or roughness science rule was introduced.
- `.10.12` remains FIELD VALIDATION PENDING until a new `.10.12` CASE is run.
