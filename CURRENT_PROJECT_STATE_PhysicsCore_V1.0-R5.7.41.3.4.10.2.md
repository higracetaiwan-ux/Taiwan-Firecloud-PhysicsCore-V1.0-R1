# Taiwan Firecloud PhysicsCore — Current Project State

## 現行候選版
V1.0-R5.7.41.3.4.10.2 — Twilight Glow Molecular Numeric Route Context

## `.3.4.10.1` TWS134 Field 結果
- CASE：2026-09-13 sunset / TWS134 鰲鼓濕地。
- Analysis Integrity 72/72 PASS；CASE Integrity 32/32 PASS。
- Observer Spectral Extinction：21.376 s（`.3.4.10` TWS106）→ 11.765 s（`.3.4.10.1` TWS134），約 −45%；兩案例不同地點，不比較 Glow total，但 component Field reduction + prior same-input exact A/B 足以關閉 `.3.4.10.1` gate。
- Glow 新第一大戶：Volume Assembly 25.414 s。

## `.3.4.10.2` 任務
- 把 Glow Volume Assembly 內重複的 molecular T/P pandas conversion 與 lower-boundary scan 改為 route-scoped numeric context。
- Rayleigh/local molecular readiness 與 HITRAN species readiness保持分離。
- 不改 10 m endpoint tolerance、1 m quantization、ML137 near-surface bridge、Rayleigh/HITRAN 或六波段。

## Actual CASE local gate
- TWS134 1092 volumes：Rayleigh / local molecular state / boundary diagnostics 全部 exact-equivalent。
- helper runtime 約 4.07 s → 0.30 s（13.7×）；不作 Field speedup 宣稱。
- Working-tree full regression：659/659 PASS。
- Final fresh-extract regression：659/659 PASS。

## 已關閉 runtime milestones
- `.3.4.8` Viewing Path Geometry：FIELD PASS。
- `.3.4.9` Red-Light Hotspot Decomposition：FIELD PASS。
- `.3.4.9.1` cache mechanism PASS；runtime hypothesis NOT FIELD PASS。
- `.3.4.9.2` precipitation horizontal-support ray reuse：FIELD PASS。
- `.3.4.10` Twilight Glow profiler：FIELD PASS。
- `.3.4.10.1` Observer Aerosol Numeric Route Context：FIELD PASS。

## Science baseline
`R5.7.41.2_SHADOW_COT_AB_FROZEN`；Production COT、Shadow promotion gates、Formation / Viewing / Glow independence 全部維持凍結。
