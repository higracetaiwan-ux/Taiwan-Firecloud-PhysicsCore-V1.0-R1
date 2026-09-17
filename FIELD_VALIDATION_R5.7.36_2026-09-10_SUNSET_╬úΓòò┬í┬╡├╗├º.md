# Taiwan Firecloud PhysicsCore V1.0-R5.7.36
## 2026-09-10 Sunset CASE 實地驗證報告

### 一、驗證結論

本次 CASE 可確認 **R5.7.36 沒有出現低雲誤升格為 Formation Canvas 的回歸**，且新加入的 `FORMATION_CANVAS_LOW_CLOUD_ROLE_SEPARATION` Integrity 檢查為 **PASS**。

但整體 Analysis / CASE Integrity 尚未全綠，唯一真正的上游硬失敗仍是既知的 **Near-Surface Molecular Boundary** 問題，因此 R5.7.37 的處理方向仍然正確，且不需要放寬原本 10 m tolerance。

### 二、Integrity

Analysis Integrity：56 PASS / 2 FAIL。

FAIL：
- `TWILIGHT_GLOW_OBSERVER_DEEP_RANGE_MOLECULAR_COVERAGE`
- `ANALYSIS_INTEGRITY_OVERALL`（由上項連帶造成）

Case Integrity：21 PASS / 2 FAIL；兩個 FAIL 都是上游 Analysis Integrity 傳遞，CASE archive 本身仍成功輸出。

### 三、R5.7.36 Formation Canvas Eligibility

`v1_cloud_layers.csv`：3156 rows；其中 `<2 km` 低雲 1381 rows，低雲被升格為 Formation Canvas = **0**。

`v1_canvas_candidates.csv`：
- 441 rows
- `formation_canvas_eligible=True`：441 / 441
- `formation_cloud_role=FORMATION_CANVAS_TARGET`：441 / 441
- 雲底高度：約 13.435–13.447 km
- Primary Canvas 0–40 km：351 rows
- Extended Canvas 40–100 km：90 rows

注意：本次 1381 個 `<2 km` 低雲全部在 100 km 以外，因此此 CASE 沒有直接重現先前日本 CASE 的「0–100 km 低雲」壓力場景。若要正式 FIELD CLOSE R5.7.36 的低雲角色分離，仍建議再用 R5.7.36 跑一次具有 0–100 km 低雲的日本 CASE。

### 四、R5.7.35.2 Viewing precipitation contract

Viewing eligible targets：441。

`v1_viewing_precipitation_evidence.csv`：441 rows，missing=0；`VIEWING_PRECIPITATION_TARGET_COVERAGE = PASS`。

其中：
- `VIEW_PRECIPITATION_OPTICS_RESOLVED`：402
- `VIEW_PRECIPITATION_GEOMETRY_UNRESOLVED`：39

這證明 R5.7.35.2 沒有把「有 eligible target 時必須提供 precipitation evidence」的硬規則放寬。

### 五、Near-Surface Molecular Boundary

`TWILIGHT_GLOW_OBSERVER_DEEP_RANGE_MOLECULAR_COVERAGE`：153 / 156 resolved。

3 個 unresolved 全部集中在：
- 太陽高度：−6.0°
- 方向：−5° / 0° / +5°
- distance：100 km
- scatter altitude：3.75 km

0° 到 −5.5°：raw lowest-boundary gap 約 0.009713 km = 9.713 m，符合 frozen `<=10 m` tolerance。

−6°：raw gap 約 0.021319 km = 21.319 m，超過 frozen 10 m tolerance，所以 Rayleigh / gas-species 正確保持 Partial，missing=`GAS;GAS_SPECIES;RAYLEIGH`。

### 六、Aerosol Scattering

R5.7.35 / R5.7.35.1 aerosol chain 沒有回歸：
- target coverage PASS
- schema PASS
- numeric closure PASS
- provenance PASS
- missing-reason coverage PASS

1092 Glow volumes：
- Aerosol proxy READY：136
- UNRESOLVED：956
- UNRESOLVED 但 missing reason 空白：0

### 七、CAMS Runtime

8 個 CAMS request 全部 OK，timeout=0，request reattach=0。

Performance：
- `CAMS_PREFETCH_TOTAL`：345.89 秒
- `ALL_ANGLES_PHYSICS_TOTAL`：381.53 秒
- `TOTAL_ANALYSIS_CORE`：986.07 秒
- `TOTAL_TO_CASE_ARCHIVE`：1018.85 秒，約 16 分 59 秒
- Peak RSS：約 907.6 MB

未見明顯 R5.7.36 runtime regression。

### 八、正式判定

- **R5.7.36 Code / Regression：CLOSED**
- **本次 CASE 的 Formation Canvas contract：PASS**
- **低雲錯誤升格：0**
- **R5.7.35.2 positive-path precipitation handoff：PASS**
- **R5.7.35 / 35.1 aerosol chain：PASS**
- **整體 CASE：NOT FULL PASS**
- 唯一上游阻塞：Near-Surface Molecular Boundary 3 rows

下一主線仍應是 **R5.7.37 Near-Surface Molecular Boundary Closure**，並繼續保留原本 10 m tolerance，以真實近地層 evidence 補足 surface → lowest native pressure level。
