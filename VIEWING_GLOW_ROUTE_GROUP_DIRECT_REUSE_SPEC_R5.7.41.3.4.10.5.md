# R5.7.41.3.4.10.5 — Viewing / Glow Route Group Direct Reuse Spec

## 目的

降低 `build_viewing_spectral_extinction()` 在每個 Viewing / Twilight Glow target 上重複建立 pandas boolean-sliced route DataFrame 的成本，保持所有物理積分、排序、Missing semantics 與六波段輸出完全不變。

## 問題

`prepare_viewing_spectral_runtime_context()` 已依 exact `time + solar_altitude_deg + direction_offset_deg` 建立 route groups，但舊 builder 對每個 target 仍再次執行：

- aerosol group：`distance_km <= target_distance`
- gas group：`distance_km <= target_distance`

Glow 1092 targets 因而產生 2184 次重複 DataFrame boolean filtering / materialization。

這些 slicing 對物理結果並非必要：

- `_integrate_view_aerosol()` / `_integrate_view_aerosol_prepared()` 本身依 target distance 截斷 segment。
- `_integrate_view_gas()` 本身只取 `distance <= target_distance`，必要時再 append target endpoint。

## `.10.5` 實作

Builder 直接重用 exact route group：

```text
ar = aerosol_groups.get(k, empty)
gr = gas_groups.get(k, empty)
```

不再在 builder 層做 per-target DataFrame slicing。

## 不變項

- Formation / Viewing / Twilight Glow 分離不變。
- 六波段 550/575/600/650/700/750 nm 不變。
- CAMS native aerosol interpolation 不變。
- HITRAN/LUT / gas spectroscopy 不變。
- Cloud LOS / COT / blocker semantics 不變。
- precipitation 不變。
- `Missing ≠ Clear ≠ Zero` 不變。
- target distance bound 仍由各 integrator 原生邏輯執行。
- row / segment accumulation order 不變。

## Actual TWS134 A/B

使用 `.10.4` CASE 同一批資料：

- Glow 1092 targets：baseline 約 2.50 s；`.10.5` 約 2.01–2.19 s。
- Main Viewing 585 targets：baseline 約 1.50 s；`.10.5` 約 1.24–1.33 s。
- 兩者皆 `pd.testing.assert_frame_equal(..., check_dtype=True, check_exact=True)` PASS。

以上只屬同輸入 local benchmark；`.10.5` Field PASS 仍須新 CASE 驗證 `TWILIGHT_GLOW_COMPONENT_OBSERVER_SPECTRAL_EXTINCTION`。
