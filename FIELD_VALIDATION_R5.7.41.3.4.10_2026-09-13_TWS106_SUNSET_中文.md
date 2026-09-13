# Field Validation — R5.7.41.3.4.10 / 2026-09-13 TWS106 Sunset

## CASE
- Version：`1.0.0-R5.7.41.3.4.10`
- Site：TWS106 高美濕地
- Event：2026-09-13 sunset
- CASE members：132

## Integrity
- Analysis Integrity：72/72 PASS
- CASE Integrity：32/32 PASS

## Twilight Glow profiler
- `TWILIGHT_GLOW_INDEPENDENT_BRANCH`：60.523 s
- 10 components 合計：60.429 s（99.84%）

| Component | 秒 | Glow 占比 |
|---|---:|---:|
| Observer Spectral Extinction | 21.376 | 35.3% |
| Volume Assembly | 19.551 | 32.3% |
| Observer Precipitation | 10.930 | 18.1% |
| Lookup Context Prep | 6.310 | 10.4% |
| Aerosol Scattering | 1.561 | 2.6% |
| Summary | 0.283 | 0.5% |
| Geometry | 0.243 | 0.4% |
| Aerosol Summary Attach | 0.107 | 0.2% |
| Targets | 0.064 | 0.1% |
| Phase1 Exports | 0.005 | <0.1% |

## Function-level follow-up
Actual-CASE reconstruction showed `_integrate_view_aerosol()` dominates `build_viewing_spectral_extinction()` because each target repeatedly filters the same CAMS route and rebuilds pressure-level ext532 arrays. This supports `.3.4.10.1` numeric route-context optimization.

## Other runtime
- Total Analysis Core：617.121 s
- Total to CASE archive：642.380 s
- CAMS Prefetch：215.692 s
- Secondary forecast native optics prefetch：84.372 s
- Gas + Spectral RT：40.701 s
- Red-Light total：30.575 s
- Cloud 3D optical blocking：29.101 s
- CASE export：25.258 s

Provider I/O is not used to rank Glow internal CPU components.
