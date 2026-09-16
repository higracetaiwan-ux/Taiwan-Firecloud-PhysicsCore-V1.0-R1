# Ice Microphysics Phase 2 Step 2 — Source Capability Survey

版本：`R5.7.41.3.4.10.13`  
證據日期：2026-09-16  
Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`  
模式：`SOURCE_CAPABILITY_SURVEY_ONLY`

## 目的

本階段只回答一件事：目前有哪些 authoritative external forecast/model sources，真的能提供 PhysicsCore Ice Optics 所需的 Dmax／PSD／number concentration／effective-size 證據？

不得因欄位名稱相似或存在冰水質量，就自行推導 Yang/Bi `maximum_dimension_um`。本階段不下載新 provider、不新增 microphysics mapping、不改 Formation／Viewing／Twilight Glow，也不開啟 production Ice Optics。

## 調查結論

| Source | 台灣 operational coverage | 已確認的冰雲微物理 | 分類 | 可直接做 Dmax/PSD？ |
|---|---:|---|---|---:|
| NOAA GFS 0.25° | 是 | ICMR / SNMR / GRLE 等 bulk mass | `MASS_ONLY` | 否 |
| DWD ICON Global Open | 是 | `qi`、`tqi` 等 bulk mass / column mass | `MASS_ONLY` | 否 |
| ECMWF IFS Open Data subset | 是 | 公開 subset 沒有 cloud-ice size / number / PSD；`ciwc` 不是目前 open parameter table 成員 | `CONTEXT_ONLY` | 否 |
| ECMWF IFS radiation effective-size diagnostic | 參考 | radiation scheme 的 ice effective diameter/radius | `EFFECTIVE_RADIUS_ONLY|REFERENCE_ONLY` | 否，effective size ≠ Yang/Bi Dmax |
| NASA GEOS-FP 5.43.0 | 是 | forecast-capable state collection 有 QI / QS 等 bulk mass | `MASS_ONLY` | 否 |
| NOAA RAP | 否（北美） | CIMIXR + NCCICE | `MASS_PLUS_NUMBER_MOMENT|REFERENCE_ONLY` | 否；需 scheme-specific PSD/mass-size contract |

因此目前正式狀態固定為：

- `TAIWAN_DIRECT_DMAX_SOURCE_AVAILABLE=false`
- `TAIWAN_PSD_SOURCE_AVAILABLE=false`
- `DMAX_SOURCE_SELECTION_ELIGIBLE=false`
- `PSD_SOURCE_SELECTION_ELIGIBLE=false`
- `PRODUCTION_ICE_OPTICS_READY=false`
- `physics_promotion_allowed=false`
- `eligibility_state=NO_AUTHORITATIVE_TAIWAN_SIZE_OR_PSD_SOURCE`

## 來源依據

### NOAA GFS

NCEP operational GFS GRIB inventory 顯示 cloud-ice mass (`ICMR`) 與其他 hydrometeor mass fields，但未顯示 direct Dmax、ice effective radius、ice number concentration 或 PSD bins。

Reference: https://www.nco.ncep.noaa.gov/pmb/products/gfs/

### DWD ICON Global Open

DWD global open-data directory存在 `qi`、`tqi` / `tqi_dia` 等冰水質量產品；本次調查的 global directory沒有 `qni/` entry。這只證明 mass evidence，不構成 PSD 或 Dmax。

Reference: https://opendata.dwd.de/weather/nwp/icon/grib/00/

### ECMWF IFS

ECMWF 目前 public Open Data parameter table（Cycle 50r1）不列 `ciwc`、ice number concentration、direct particle size 或 PSD fields；ECMWF Parameter Database 另證明 `ciwc` 是「specific cloud ice water content」的 bulk-mass semantic，但這不能等同粒徑。

IFS radiation documentation另定義 ice effective diameter/radius 診斷。即使取得 effective size，也不可直接當 Yang/Bi maximum dimension；任何 `r_eff/De → Dmax` 都需要獨立、版本化、可驗證 mapping contract。

References:
- https://www.ecmwf.int/en/forecasts/datasets/open-data
- https://codes.ecmwf.int/grib/param-db/?id=247
- https://www.ecmwf.int/en/publications/ifs-documentation

### NASA GEOS-FP

2026 GEOS-FP File Specification v2.0（GEOS-5.43.0）在 forecast-capable assimilated-state collections列出 `QI / QL / QR / QS`；文件中沒有 `RICE` direct effective-radius/Dmax field。標準 `tavg3_3d_cld_Nv` cloud diagnostics也沒有被標示為 forecast-mode standard collection。

Reference: https://gmao.gsfc.nasa.gov/publications/office_notes/

### NOAA RAP

RAP product inventory顯示 `CIMIXR`（cloud-ice mass mixing ratio）與 `NCCICE`（number concentration of cloud ice）可同時存在，這對未來「二矩量 microphysics contract」非常有研究價值。但 RAP 官方範圍為 North America，因此不可當台灣 operational source；而且 mass+number 仍需要該 microphysics scheme 的 PSD form、mass-size/density/habit 定義才能合法映射粒徑。

References:
- https://www.nco.ncep.noaa.gov/pmb/products/rap/
- https://rapidrefresh.noaa.gov/

## 凍結規則

以下捷徑在 `.10.13` 明確禁止：

- effective radius → Dmax（沒有 validated contract 時）
- effective diameter → Dmax（沒有 validated contract 時）
- IWC / IWP → Dmax
- temperature → Dmax
- RH / cloud fraction → Dmax
- mass + number concentration → Dmax（沒有 scheme-specific distribution contract 時）
- assumed PSD
- fixed habit default
- fixed roughness default
- reference-only source 當成 Taiwan operational source

## 下一步

`.10.13` FIELD PASS 後，Phase 2 Step 3 才能研究「候選 scheme-specific mapping contract」。優先順序應是：

1. 尋找 global/Taiwan-capable、可取得的 ice number concentration 或多矩量 forecast source。
2. 若只有 effective radius，先證明其定義與 Yang/Bi Dmax 的可轉換性，而不是直接套比例。
3. 若使用 mass + number，必須取得同一 microphysics scheme 的 PSD functional form、mass-size relation、particle density/habit semantics、validity domain與 validation evidence。
4. 任何 mapping 先維持 diagnostic/shadow mode，通過獨立 validation 才能另開 production promotion gate。
