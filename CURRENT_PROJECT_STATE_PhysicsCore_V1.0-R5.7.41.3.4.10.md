# Taiwan Firecloud PhysicsCore — Current Project State

## 現行候選版
V1.0-R5.7.41.3.4.10 — Twilight Glow Runtime Hotspot Decomposition

## 已關閉 runtime milestones
- `.3.4.8` Viewing Path Geometry Optimization：FIELD PASS。
- `.3.4.9` Red-Light Hotspot Decomposition：FIELD PASS。
- `.3.4.9.1` native hydrometeor context reuse：cache mechanism PASS，但 runtime hypothesis NOT FIELD PASS。
- `.3.4.9.2` horizontal-support ray reuse：FIELD PASS；precipitation path 109.515 → 6.777 s（-93.8%，約 16.2×），Red-Light total 152.332 → 45.305 s（-70.3%），science exact-equivalent。

## `.3.4.9.2` 第二跑
- Total core 819.767 → 475.024 s，主要來自 CAMS/GFS cache reuse。
- CAMS 5/5 prior-run persistent cache hit；GFS 0 network。
- DWD 並非 warm repeat：provider cycle 00Z/lead10 → 06Z/lead4，因此 158 network requests / 171.9 MB。
- Open-Meteo request keys相同，但預設 1800 s TTL 已過期，7/7 重新抓取。
- categorical Formation / Viewing / Photography / Red-Light / Glow / operational decision 保持一致；numeric forecast evidence 可因新 provider cycle 合理改變。

## 現在最大穩定非-provider CPU stages
1. Twilight Glow: ~90.98 s
2. Gas + Spectral RT: ~48.28 s
3. Red-Light: ~45.94 s
4. Cloud 3D Optical Blocking: ~41.58 s
5. CASE export: ~40.88 s
6. Viewing + Photography: ~35.55 s

## `.3.4.10` 任務
只拆 Twilight Glow 10 個 runtime components，不改 science。Field CASE 後依最大 component 再做 exact-equivalent optimization。

## Local gates
- Glow targeted regression 39/39 PASS
- Full regression 650/650 PASS
- FULL-CLEAN fresh-extract 650/650 PASS
- profiler ON/OFF Glow detail + summary exact equality

## Science baseline
`R5.7.41.2_SHADOW_COT_AB_FROZEN`；Production COT、Shadow promotion gates、Formation / Viewing / Glow independence 全部維持凍結。
