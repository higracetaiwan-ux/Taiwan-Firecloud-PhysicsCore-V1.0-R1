# Taiwan Firecloud PhysicsCore — Current Project State

## Current release

**V1.0-R5.7.41.3.4.10.5 — Viewing / Glow Route Group Direct Reuse**

Science baseline remains frozen at **R5.7.41.2_SHADOW_COT_AB_FROZEN**.

## 最新 Field 結果

`.3.4.10.4｜2026-09-13 sunset｜TWS134`：

- Analysis Integrity 72/72 PASS
- CASE Integrity 32/32 PASS
- Glow Observer Spectral Extinction 8.533 → 6.642 s（−22.2%）
- Glow total 25.573 → 23.364 s
- CAMS cycle 由 2026-09-12 12Z f021 更新為 2026-09-13 00Z f009，所以 `.10.3 ↔ .10.4` 不是固定 provider snapshot replay，science CSV 不要求 byte-identical。
- `.10.4` 同一批 TWS134 input 做 memo ON/OFF：1092 targets `check_exact=True`，full observer spectral 約 3.82 → 2.50 s。
- `.3.4.10.4 = FIELD PASS`。

## `.3.4.10.5` 工作

函式級 profiling 顯示 spectroscopy memo 後，observer spectral 的大量剩餘成本來自 pandas route slicing / cloud-row materialization。

先測試 Cloud horizontal-support ray memo：9672 ray calls 僅降至約 9048，沒有可重現整體加速，**候選已淘汰，未納入 release**。

`.10.5` 改為更小風險的 route-group direct reuse：

- shared runtime context 已依 exact time/angle/direction 建 route groups；
- builder 不再對每 target 重新做 aerosol/gas `distance<=target_distance` DataFrame slicing；
- target distance bound 仍由既有 integrators 內部處理；
- TWS134 Glow 1092 targets 與 Main Viewing 585 targets 均 `check_exact=True`。

Working-tree regression：670/670 PASS。

## Runtime roadmap

1. 部署 `.10.5`，仍測 TWS134 / 2026-09-13 sunset。
2. Field gate：`TWILIGHT_GLOW_COMPONENT_OBSERVER_SPECTRAL_EXTINCTION` 應從 `.10.4` 的 6.642 s 再下降。
3. 若 `.10.5` PASS，再重新 profile cloud-row materialization / gas interpolation，不預先更動 physics。
4. Shadow COT 維持 diagnostic-only validation cohort；不得 promotion。
5. Genuine Tier-2 directional scattering 仍需外部 libRadtran/MYSTIC。
