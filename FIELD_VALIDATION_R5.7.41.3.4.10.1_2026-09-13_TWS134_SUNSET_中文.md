# R5.7.41.3.4.10.1 Field Validation — 2026-09-13 TWS134 鰲鼓濕地 Sunset

## CASE
- 版本：`1.0.0-R5.7.41.3.4.10.1`
- 景點：TWS134 鰲鼓濕地，嘉義縣
- 事件：2026-09-13 sunset
- Glow volumes：1092（13 angles × 3 directions × 28 volumes）
- Analysis Integrity：72/72 PASS
- CASE Integrity：32/32 PASS

## `.3.4.10.1` Field gate
`.3.4.10` TWS106 profiler 的 `TWILIGHT_GLOW_COMPONENT_OBSERVER_SPECTRAL_EXTINCTION` 為 21.375611 s；本次 `.3.4.10.1` TWS134 為 11.765421 s，下降約 44.96%。兩次景點不同，因此 Glow total 不作直接 A/B speedup 宣稱；但兩案均為 1092-volume 固定結構，且 `.3.4.10.1` 在 TWS106 actual-case 已以相同輸入完成 1092-row `check_exact=True`，本次 Field component reduction 足以關閉此 runtime optimization gate。

## Glow 10-component profiler
- Total Glow：62.651712 s
- Observer Spectral Extinction：11.765421 s
- Volume Assembly：25.413994 s
- Observer Precipitation：13.524997 s
- Lookup Context Prep：8.854904 s
- Aerosol Scattering：2.104501 s
- Geometry：0.292422 s
- Summary：0.340989 s
- Aerosol Summary Attach：0.158500 s
- Targets：0.077191 s
- Phase1 Exports：0.005539 s

目前第一大戶已轉為 `TWILIGHT_GLOW_COMPONENT_VOLUME_ASSEMBLY = 25.413994 s`。

## 其他 runtime
- Red-Light total：44.356288 s
- Red-Light precipitation：6.501342 s，`.3.4.9.2` Phase 2 改善仍維持低成本。
- Viewing + Photography：39.595011 s
- Total Analysis Core：684.363452 s
- Total to CASE archive：718.701457 s

本 CASE 為 provider-cold：CAMS 5 network requests / 221.236 s；DWD 184 network requests / 247,708,483 bytes；因此總 runtime 不用來評估 `.3.4.10.1` CPU optimization。

## 結論
- `.3.4.10.1 Observer Aerosol Numeric Route Context`：**FIELD PASS**。
- Science baseline 未改：`R5.7.41.2_SHADOW_COT_AB_FROZEN`。
- 下一個 Glow runtime 目標：Volume Assembly；actual-case function profiling 顯示 molecular T/P profile / lower-boundary diagnostics 有大量重複 pandas 轉換，可做 exact-equivalent numeric route context。
