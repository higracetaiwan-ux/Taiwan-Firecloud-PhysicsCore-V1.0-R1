# Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.4 Release Notes

## 名稱

**Viewing / Glow Gas Spectroscopy State Memo**

## 變更摘要

- 版本提升為 `1.0.0-R5.7.41.3.4.10.4`。
- `.3.4.10.3` TWS134 Field：Observer Precipitation 14.309 → 5.463 s；`.10.3` 正式 FIELD PASS。
- 新增 `viewing_spectral.py` process-local gas sigma memo。
- memo 僅在 spectroscopy LUT content signature、gas、wavelength、exact T、exact P 全部相同時重用。
- 不修改 `gas_rt.py`、HITRAN/LUT、Gas RT formulas 或任何 science threshold。

## 驗證

TWS134 actual gas evidence：

- 1092 Glow targets
- legacy gas helper：1.601 s
- memo gas helper：0.509 s
- 約 3.14×
- **1092/1092 exact equality**
- memo entries：4752
- LUT signature groups：1

TWS134 isolated full observer spectral A/B：

- output CSV SHA256 完全相同
- baseline 約 3.24 s
- memo 約 2.17 s

上述為離線 benchmark，不宣稱 Field speedup；Field PASS 仍需新 CASE 驗證 `TWILIGHT_GLOW_COMPONENT_OBSERVER_SPECTRAL_EXTINCTION`。
