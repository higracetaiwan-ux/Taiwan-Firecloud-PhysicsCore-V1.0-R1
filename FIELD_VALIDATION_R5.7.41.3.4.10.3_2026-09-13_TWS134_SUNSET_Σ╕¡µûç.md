# R5.7.41.3.4.10.3 Field Validation — 2026-09-13 TWS134 Sunset

## 結論

**R5.7.41.3.4.10.3 Twilight Glow Observer Precipitation Horizontal-Support Ray Reuse = FIELD PASS。**

同一景點 TWS134、同一事件 2026-09-13 sunset 與 `.3.4.10.2` 做 A/B：

- `TWILIGHT_GLOW_COMPONENT_OBSERVER_PRECIPITATION`：**14.309 s → 5.463 s**，約 **−61.8% / 2.62×**。
- `TWILIGHT_GLOW_INDEPENDENT_BRANCH`：**42.331 s → 25.573 s**，約 **−39.6%**。
- Analysis Integrity：**72/72 PASS**。
- CASE Integrity：**32/32 PASS**。

## Glow 重新排名（.10.3）

1. Observer Spectral Extinction：**8.533 s**（33.37%）
2. Observer Precipitation：**5.463 s**（21.36%）
3. Lookup Context Prep：**4.821 s**（18.85%）
4. Volume Assembly：**4.498 s**（17.59%）
5. Aerosol Scattering：**1.524 s**（5.96%）

其餘 component 均低於 0.3 s。

## Science exactness

`.3.4.10.2` 與 `.3.4.10.3` 兩個 TWS134 CASE 各 132 members：

- common members：132
- byte-identical：105
- differences：27
- **67/67 個 `v1_*.csv` 全部 byte-for-byte identical**。

差異集中在 provider/raw/runtime/manifest/job 類資料與 `summary.csv` 的執行資訊；所有 V1 science outputs 完全一致。因此此次加速不是減少 pressure levels、改變 hydrometeor extinction 或放寬 Missing semantics。

## 仍凍結不變

- Cloud→Observer 17-point LOS sampling
- 所有 native pressure levels
- RWMR / SNMR / GRLE microphysics
- `Q_EXT_VISIBLE = 2.0`
- 六波段 550/575/600/650/700/750 nm
- Missing ≠ Clear ≠ Zero
- Formation / Viewing / Twilight Glow 分支語意
- Earth Shadow / Production COT / Shadow COT 規則

## 下一個 runtime target

`.10.3` Field 後 Glow 第一大戶變成 `TWILIGHT_GLOW_COMPONENT_OBSERVER_SPECTRAL_EXTINCTION = 8.533 s`。

函式級 profiling 顯示 spectral extinction 內主要剩餘成本為 Gas RT 與 observer-cloud LOS。Gas RT 中 1092 Glow targets 形成 8736 gas segments，但 exact T/P 狀態只有 264 組跨 route 重複；legacy `_sigma_fast()` 因六波段 × 三氣體被重複呼叫約 157k 次。因此下一步優先做 content-scoped spectroscopy-state memo，保持 HITRAN/LUT 與逐段乘法順序不變。
