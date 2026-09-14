# R5.7.41.3.4.10.2 Field Validation — 2026-09-13 TWS134 Sunset

## 結論
`R5.7.41.3.4.10.2 Twilight Glow Molecular Numeric Route Context`：**FIELD PASS**。

同地點 TWS134 對照 `.3.4.10.1`：

- `TWILIGHT_GLOW_COMPONENT_VOLUME_ASSEMBLY`: **25.413994 s → 6.046533 s**（-76.21%，約 4.20×）
- `TWILIGHT_GLOW_COMPONENT_LOOKUP_CONTEXT_PREP`: **8.854904 s → 6.137002 s**（-30.69%）
- `TWILIGHT_GLOW_INDEPENDENT_BRANCH`: **62.651712 s → 42.331395 s**（-32.43%）
- Analysis Integrity: **72/72 PASS**
- CASE Integrity: **32/32 PASS**

因此 `.10.2` 沒有把 Volume Assembly 的成本搬移到 Lookup Context Prep，Field gate 成立。

## `.10.2` 後 Glow component 排名

1. Observer Precipitation: **14.309378 s**
2. Observer Spectral Extinction: **12.592051 s**
3. Lookup Context Prep: **6.137002 s**
4. Volume Assembly: **6.046533 s**
5. Aerosol Scattering: **2.135180 s**

新的第一優先 runtime target 為 `OBSERVER_PRECIPITATION`。

## Science contract
`.10.2` 只數值化相同 route 的 molecular T/P 與 lower-boundary metadata；Rayleigh、local molecular state、HITRAN gas、10 m boundary tolerance、六波段、Missing semantics 皆未更改。
