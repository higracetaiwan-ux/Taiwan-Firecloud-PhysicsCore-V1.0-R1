# Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.5 Release Notes

## 名稱

**Viewing / Glow Route Group Direct Reuse**

## 變更摘要

- 版本提升為 `1.0.0-R5.7.41.3.4.10.5`。
- `.3.4.10.4` TWS134 Field：Glow Observer Spectral Extinction 8.533 → 6.642 s；配合同輸入 memo ON/OFF exact A/B，`.10.4` 正式 FIELD PASS。
- `build_viewing_spectral_extinction()` 不再對每個 target 重複建立 aerosol / gas `distance <= target_distance` DataFrame slices。
- 直接重用已由 shared runtime context 建立的 exact time/angle/direction route groups。
- target-distance 截斷仍由原 aerosol/gas integrator 執行，物理積分與 fail-close semantics 不變。

## Actual TWS134 local benchmark

- Glow 1092 targets：baseline 約 2.50 s；`.10.5` 約 2.01–2.19 s；**check_exact=True**。
- Main Viewing 585 targets：baseline 約 1.50 s；`.10.5` 約 1.24–1.33 s；**check_exact=True**。

上述為 local same-input benchmark，不宣稱 Field speedup。
