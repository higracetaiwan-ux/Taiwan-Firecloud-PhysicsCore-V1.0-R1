# R5.7.41.3.4.10.5 Field Validation — 2026-09-13 TWS134 Sunset

## 結論

**Science exactness PASS；runtime hypothesis NOT FIELD PASS。**

`.10.4 ↔ .10.5` 為同一 TWS134 / 2026-09-13 sunset，且 CAMS/GFS/DWD forecast snapshot 相同：

- CAMS：2026-09-13 00Z / lead 9 h
- GFS：2026-09-13 06Z / f003
- DWD ICON：2026-09-13 06Z / lead 4 h
- Open-Meteo canonical cache keys 相同

## Integrity

- Analysis Integrity：**72/72 PASS**
- CASE Integrity：**32/32 PASS**

## Science exactness

- 共同 `v1_*.csv`：**67/67 byte-for-byte identical**
- 因此 `.10.5` route-group direct reuse 沒有造成 Formation / Viewing / Red-Light / Glow / Shadow / COT 等 science output 漂移。

## Runtime Field gate

| Stage | `.10.4` | `.10.5` | 變化 |
|---|---:|---:|---:|
| Twilight Glow Observer Spectral Extinction | 6.642360 s | 7.084513 s | +6.7% |
| Observer Precipitation | 5.270388 s | 7.511858 s | +42.5% |
| Lookup Context Prep | 4.670006 s | 7.239923 s | +55.0% |
| Volume Assembly | 4.569430 s | 7.054311 s | +54.4% |
| Twilight Glow total | 23.363876 s | 32.202235 s | +37.8% |
| TOTAL_ANALYSIS_CORE | 670.991475 s | 674.625555 s | +0.5% |

`.10.5` local same-input benchmark 曾顯示小幅加速，但 Field 上沒有可重現收益，因此不得標為 FIELD PASS。

## Provider I/O 注意

`.10.5` CAMS Spectral Column AOD 為 41.762 s，`.10.4` 為 147.938 s；provider I/O 反而變快。因此 Total Core 幾乎持平不能用來替 `.10.5` 辯護，Field gate 應以被修改的 Observer Spectral Extinction component 判斷。

## 下一步

Actual-case function profile 顯示 `_cloud_expected_tau()` 的 cloud DataFrame copy/filter/iterrows 是剩餘 observer spectral 的主要可移除 runtime overhead。下一版採 exact-order Cloud Numeric Route Context，不改 25-point LOS、COT/CF、occupancy expectation 或 Missing/conflict semantics。
