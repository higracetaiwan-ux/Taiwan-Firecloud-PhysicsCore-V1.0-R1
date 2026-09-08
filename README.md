# Taiwan Firecloud PhysicsCore V1.0-R5.7.23

正式來源基線：**R5.7.22.1 ACCEPTED BASELINE**。

R5.7.23 同時完成兩條工程主線：

1. **Runtime Hardening**：Cold/Warm/Resume、cache provenance、atomic cache、CAMS ADS single-flight、stage heartbeat、resource telemetry。
2. **Genuine Liquid-Cloud Full Directional Calibration Pipeline V3**：REAL CASE domain → spherical MYSTIC jobs → external result collector/QC → production LUT package gate。

本建置環境沒有 `uvspec`，所以 genuine calibrated directional LUT **尚未生成／尚未安裝**；不得以 synthetic LUT 取代。

### Runtime Cold Test

UI 勾選 Cold Test 後，本次 job 使用隔離 provider cache namespace。CASE 會新增：

- `runtime_execution_contract.csv`
- `runtime_cache_provenance.csv`
- `runtime_stage_trace.csv`
- `runtime_resource_telemetry.csv`

### Calibration CLI

由 CASE 推導 domain：

```bash
python tools/derive_tier2_liquid_directional_domain_from_case.py --case <CASE.zip_or_dir> --output-dir <domain_dir>
```

建立 calibration bundle：

```bash
python build_tier2_liquid_directional_calibration_jobs.py --foundation-csv <foundation.csv> --readiness-csv <readiness.csv> --output-dir <bundle_dir>
```

在外部 libRadtran 環境先渲染 jobs（不執行 RT）：

```bash
python run_tier2_libradtran_mystic_calibration.py --jobs-csv <jobs.csv> --solver-recipe-json <recipe.json> --run-dir <run_dir> --data-files-path <libRadtran/data> --atmosphere-file <atm.dat> --render-only
```

真正 external MYSTIC 執行後收集結果：

```bash
python collect_tier2_libradtran_mystic_results.py --jobs-csv <jobs.csv> --run-dir <run_dir> --output-csv <results.csv> --solver-version <version>
```

最後 production build 必須同時提供 exact domain spec 與 calibration metadata：

```bash
python build_tier2_liquid_directional_lut_from_results.py --jobs-csv <jobs.csv> --results-csv <results.csv> --metadata-json <metadata.json> --domain-spec-json <domain.json> --output-dir <lut_package_dir>
```

詳見：

- `RUNTIME_HARDENING_SPEC_R5.7.23.md`
- `TIER2_LIQUID_DIRECTIONAL_CALIBRATION_PIPELINE_SPEC_R5.7.23.md`

## R5.7.23 Genuine Liquid-Cloud Full Directional Calibration Pipeline

本版以 **R5.7.22.1 ACCEPTED BASELINE** 為唯一基準，不改動 Route Invariance、Formation / Viewing / Glow 分離或六波段契約。新增 production calibration 生產線：

`REAL Tier-2-ready liquid targets → calibration domain → libRadtran/MYSTIC spherical jobs → external RT QC → calibrated directional LUT package`

- Production LUT 軸維持 `COT × r_eff × θ₀ × θᵥ × Δφ × wavelength`。
- `cloud_thickness_km` 只保留為幾何／光學證據，不是 production interpolation axis。
- 第一階段只建立 **liquid cloud** genuine calibration，不以 ICE 或 synthetic response 混入。
- 外部結果必須完整覆蓋 job tensor、solver exit=0、Monte-Carlo convergence QC、approved full-hemisphere solver 與 provenance。
- 若沒有 genuine RT 結果，production LUT 必須維持 `NOT_YET_GENERATED_EXTERNAL_RT_REQUIRED`；不可用 synthetic LUT 冒充。
- 本版提供正式 job generator、MYSTIC spherical recipe/template、external-result validator 與 production package builder。


## R5.7.22.1 Route Invariance Hotfix

本版在 R5.7.22 Full Directional Cloud Scattering Geometry Contract 上修正 provider sampling route 與 runtime 太陽角度集合耦合的問題。

正式凍結：

- GFS / CAMS / Forecast 的 Reference Route 固定以太陽高度 **−2.0°** 的太陽方位建立。
- Provider spatial sampling distance lattice 固定依完整 **0°～−6°** PhysicsCore 路徑需求建立。
- 改變 runtime angle subset、或從 9-angle 擴充到 13-angle，不得旋轉或縮短既有 sampling corridor。
- 每個太陽高度仍使用自己的事件時間、太陽高度與太陽方位計算 Sun→Cloud 與 Tier-2 directional geometry。
- CASE 新增 `route_reference_contract.csv`，保存 reference angle、reference time、reference azimuth、route domain 與 invariance provenance。

此修正關閉 R5.7.21.1 / 未修正 R5.7.22 中因核心角度中點由 −2° 變成 −3°，導致 route bearing 約偏移 0.672° 的回歸。


R5.7.22 正式把 Tier-2 雲散射方向幾何由原本只依賴 `scattering_angle`，升級為完整的 target-local directional contract：

- `θ₀ = solar_zenith_deg`
- `θᵥ = view_zenith_deg`
- `Δφ = relative_azimuth_deg`
- `scattering_angle_deg` 僅保留為衍生診斷，不再是 production interpolation axis

核心火燒雲太陽高度維持：

`0, −0.5, −1, −1.5, −2, −2.5, −3, −3.5, −4, −4.5, −5, −5.5, −6°`

共 13 個角度。

## 核心架構

PhysicsCore 持續維持三個獨立問題：

- **Formation**：Sun → CloudBase，判斷火燒雲是否形成。
- **Viewing**：Cloud → Observer，判斷已形成的火燒雲是否看得到。
- **Glow**：獨立的大氣霞光分支，不取代雲底受光 Formation。

Formation 核心輸出仍分離為 Brightness、Redness、Effective Illuminated Area，不合併成單一 Formation Score。

## Tier-2 Full Directional Scattering

R5.7.22 production LUT 的核心插值維度為：

`COT × r_eff × θ₀ × θᵥ × Δφ`

六波段各自完整保留：

`550 / 575 / 600 / 650 / 700 / 750 nm`

### 方向幾何定義

- `θ₀`：Cloud → Sun 相對雲底當地天頂的夾角，範圍 0–180°。
- `θᵥ`：Cloud → Observer 相對雲底當地天頂的夾角，範圍 0–180°。
- `Δφ`：Cloud→Sun 與 Cloud→Observer 在雲底當地水平面的最小方位差，範圍 0–180°。
- `scattering_angle_deg`：Sun→Cloud incoming photon 與 Cloud→Observer outgoing photon 的夾角，只作診斷。

太陽方向會先由觀測點 local ENU 轉為 ECEF，再投影到每個 target cloud 的 local ENU；不再把觀測點太陽角度直接當成每個雲底的 local angles。

### cloud thickness 的角色

`cloud_thickness_km` 仍保留於 target / CASE 幾何與雲體證據，但 R5.7.22 不再把它當成純雲散射 LUT 的 production interpolation axis。

## Production LUT 安全閘門

R5.7.22 不接受舊版 scattering-angle-only LUT 直接升級成 production LUT。

Production LUT 必須提供：

- full directional `θ₀ / θᵥ / Δφ` 網格
- 六波段完整覆蓋
- multiple-scattering 校準來源
- full-hemisphere 0–180° 支援聲明
- RT solver provenance
- QC PASS
- validation reference
- CSV SHA256

舊 R5.7.19/R5.7.20 LUT 只保留歷史 regression 用途，不能啟動 R5.7.22 production solver。

## 跨區域時間

延續 R5.7.21：

- 依座標自動解析 IANA timezone。
- 物理時刻另外保存 UTC。
- 同一 UTC 瞬間的太陽幾何不受顯示時區影響。
- 可用日本、沖繩或其他區域作 REAL_CANVAS regression testing。

## 執行與部署

主要 Streamlit 入口：

`app.py`

完整依賴請見：

`requirements.txt`

本版文件：

- `RELEASE_NOTES_PhysicsCore_V1.0-R5.7.22.md`
- `IMPLEMENTATION_STATUS_PhysicsCore_V1.0-R5.7.22.md`
- `TIER2_DIRECTIONAL_SCATTERING_GEOMETRY_SPEC_R5.7.22.md`

## R5.7.23 Runtime Hardening

為了區分真正的 provider/runtime stall 與重新 TEST 後的 persistent-cache 加速，本版提供三種分析執行契約：`WARM_PRODUCTION`、`COLD_ISOLATED_TEST`、`RESUME_SAME_JOB`。Cold Test 會建立 job-specific provider cache namespace；CASE 另保存 runtime stage trace、cache provenance 與 resource telemetry。CAMS production 預設採 ADS global single-flight，避免兩個 forecast time 同時送出 SPECTRAL_COLUMN_AOD 等遠端請求。

R5.7.23 的 genuine liquid-cloud calibration pipeline 已可產生與驗證外部 libRadtran/MYSTIC jobs；本封裝環境未含 `uvspec`，因此 genuine calibrated production LUT 仍維持 `NOT_YET_GENERATED_EXTERNAL_RT_REQUIRED`，不會以 synthetic LUT 取代。
