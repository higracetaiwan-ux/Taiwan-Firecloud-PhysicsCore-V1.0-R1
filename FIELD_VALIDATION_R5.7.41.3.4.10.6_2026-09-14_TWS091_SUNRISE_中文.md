# R5.7.41.3.4.10.6 Field Validation — 2026-09-14 TWS091 日出

## Integrity

- Analysis Integrity：70 PASS + 1 NOT_APPLICABLE，共 71 checks。
- CASE Integrity：32/32 PASS。
- NOT_APPLICABLE：NEAR_SURFACE_MOLECULAR_BOUNDARY_BRIDGE_PROVENANCE（本次 bridged_rows=0，符合契約）。

## Performance

- TOTAL_ANALYSIS_CORE：595.768489 s
- TOTAL_TO_CASE_ARCHIVE：628.946344 s
- CAMS_PREFETCH_TOTAL：215.915299 s
- SECONDARY_FORECAST_NATIVE_OPTICS_PREFETCH：103.600418 s
- TWILIGHT_GLOW_INDEPENDENT_BRANCH：29.901809 s

Glow components：
- OBSERVER_PRECIPITATION：8.250749 s
- VOLUME_ASSEMBLY：8.073043 s
- LOOKUP_CONTEXT_PREP：7.456110 s
- OBSERVER_SPECTRAL_EXTINCTION：2.740815 s
- AEROSOL_SCATTERING：2.235353 s

## `.10.6` verdict

Observer Spectral Extinction 在不同日出事件仍維持約 2.74 s；結合 `.10.6` 開發期 Main Viewing 585/585 與 Glow 1092/1092 exact A/B，Cloud Numeric Route Context 正式判定 FIELD PASS。

## 下一瓶頸

Main Viewing precipitation 26 targets 約 8.057 s，而 Glow precipitation 1092 targets 約 8.251 s。兩者耗時近似，顯示主要成本位於每角度 native hydrometeor context preparation，而非 1092-target integration。此證據導向 `.10.7` Viewing↔Glow Shared Hydrometeor Context。
