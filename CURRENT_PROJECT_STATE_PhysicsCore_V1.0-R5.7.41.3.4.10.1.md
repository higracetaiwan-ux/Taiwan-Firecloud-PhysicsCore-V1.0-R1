# Taiwan Firecloud PhysicsCore — Current Project State

## 現行候選版
V1.0-R5.7.41.3.4.10.1 — Twilight Glow Observer Aerosol Numeric Route Context

## `.3.4.10` TWS106 Field profiler 結果
- CASE：2026-09-13 sunset / TWS106 高美濕地。
- Analysis Integrity：72/72 PASS；CASE Integrity：32/32 PASS。
- Twilight Glow total：60.523 s。10 個 component 合計 60.429 s（99.84% coverage）。
- Component 排名：Observer Spectral Extinction 21.376 s；Volume Assembly 19.551 s；Observer Precipitation 10.930 s；Lookup Context Prep 6.310 s；Aerosol Scattering 1.561 s；其餘均 <0.3 s。
- Red-Light `.3.4.9.2` 維持低成本：30.575 s total；precipitation component 約 4.73 s。

## `.3.4.10.1` 任務
- 只優化 Observer Spectral Extinction 中 CAMS aerosol route 的重複 DataFrame/pressure-profile preparation。
- 每 time/angle/direction route 建立 immutable numeric aerosol context，一次保存 native ext532 vertical arrays、explicit six-band AOD 與 temporal provenance。
- 不改 aerosol optical physics、Viewing/Glow science 或 Missing semantics。

## Actual-CASE local equivalence / benchmark
- Glow 1092 targets：legacy 6.116 s → optimized 3.440 s；DataFrame `check_exact=True`。
- Main Viewing 585 targets：legacy 3.105 s → optimized 1.843 s；DataFrame `check_exact=True`。
- Runtime-context prepare：legacy 約 1.52–1.56 s；optimized 約 2.27–2.32 s，為一次性 materialization cost。
- 上述為離線 same-input benchmark，不作 Field speedup 宣稱；需 `.3.4.10.1` 新 CASE 才關閉 Field gate。

## 已關閉 runtime milestones
- `.3.4.8` Viewing Path Geometry：FIELD PASS。
- `.3.4.9` Red-Light Hotspot Decomposition：FIELD PASS。
- `.3.4.9.1` context reuse：cache mechanism PASS；runtime hypothesis NOT FIELD PASS。
- `.3.4.9.2` precipitation horizontal-support ray reuse：FIELD PASS。
- `.3.4.10` Twilight Glow profiler：FIELD PASS（diagnostic decomposition complete）。

## Science baseline
`R5.7.41.2_SHADOW_COT_AB_FROZEN`；Production COT、Shadow promotion gates、Formation / Viewing / Glow independence 全部維持凍結。
