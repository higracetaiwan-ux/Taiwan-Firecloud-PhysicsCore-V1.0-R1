# Ice Microphysics Step 3K — Fu96 Independent Bulk Validation Qualification / Stable Serialization Hotfix

版本：`R5.7.41.3.4.10.24.1`  
Science step：`R5.7.41.3.4.10.24`  
Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`  
狀態：**QA PASS / FIELD VALIDATION PENDING**

## 科學內容
Step 3K science 不變：保留相同 Wyser number population，使用 Wyser Eq.(5) projected area 與 Fu96 geometric-optics `beta_ext≈2A_c` 對 Step 3J Yang/Bi `C_ext` diagnostic bulk extinction 做獨立 optical-kernel cross-check。

18-case scientific calculations 仍使用 full double precision；本 hotfix 不修改任何積分、Dge、beta_ext 或 k_ext 數值。

## Stable persisted evidence
為消除 `.10.24` TWS100 FIELD CASE 與 release static artifacts 的跨平台 floating byte drift，Step 3K persisted evidence / contract diagnostic values canonicalize 為 11 significant digits：

- max Fu unit-chain relative error：`1.22441956e-05`
- Step 3J vs Fu minimum relative difference：`0.26212710714`
- Step 3J vs Fu maximum relative difference：`0.31216620727`
- sample mass-area-equivalent Dge：`51.572647117 µm`
- sample solid-hex geometry Dge：`113.08468137 µm`

## Gate
```text
FU96_INDEPENDENT_OPTICAL_CROSSCHECK_EXECUTED = true
FU96_PROJECTED_AREA_CHAIN_NUMERIC_PASS = true
FU96_DGE_DUAL_SEMANTICS_SEPARATED_PASS = true
FU96_BULK_DIFFERENCE_CHARACTERIZED = true
SCIENTIFIC_BULK_VALIDATION_PASS = false
BULK_YANG_BI_PSD_INTEGRATION_ELIGIBLE = false
TAU_ICE_PRODUCTION_ALLOWED = false
PRODUCTION_ICE_OPTICS_READY = false
physics_promotion_allowed = false
```

## Frozen
Formation / Viewing / Twilight Glow / six bands / Canvas-Corridor-REZ / Earth Shadow / Production-Shadow COT / Ice runtime promotion semantics 全部不變。
