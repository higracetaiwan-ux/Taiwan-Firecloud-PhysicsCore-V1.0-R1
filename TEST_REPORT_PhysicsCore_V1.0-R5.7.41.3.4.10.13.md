# Test Report — V1.0-R5.7.41.3.4.10.13

## Targeted regression

測試集合包含：

- `.10.13` source capability registry / eligibility gate
- `.10.12` native microphysics capability audit
- `.10.12.1` Phase 2 evidence integrity gate
- `.10.10` Ice Cloud Spectral Optics shared module
- `.10.10.1` WINDY portable decoupling

結果：**35 passed / 0 failed**

## Full regression

結果：**782 passed / 0 failed / 1 existing FutureWarning**

## Fresh-extract full regression

從重新封裝的 `.10.13 FULL-CLEAN` ZIP 解壓至全新目錄後執行完整測試：**782 passed / 0 failed / 1 existing FutureWarning**。

Fresh-extract `firecloud.__version__`：`1.0.0-R5.7.41.3.4.10.13`。

Warning 來源：`tests/test_r5732_glow_observer_aerosol_coverage.py` 的 pandas DataFrame concat future behavior，非本版失敗。

## 核心斷言

- GFS / ICON / GEOS-FP mass-only 不得升格 Dmax/PSD。
- ECMWF effective-size reference 不得升格 Yang/Bi Dmax。
- RAP `CIMIXR + NCCICE` 因無台灣 coverage 且缺 scheme-specific PSD mapping contract，不得升格 operational source。
- `TAIWAN_DIRECT_DMAX_SOURCE_AVAILABLE=false`。
- `TAIWAN_PSD_SOURCE_AVAILABLE=false`。
- `PRODUCTION_ICE_OPTICS_READY=false`。
- `physics_promotion_allowed=false`。
