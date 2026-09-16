# Taiwan Firecloud PhysicsCore — Current Project State

> Version: **V1.0-R5.7.41.3.4.10.12**  
> Internal: `1.0.0-R5.7.41.3.4.10.12`  
> Development status: **IMPLEMENTATION / REGRESSION PASS — FIELD VALIDATION PENDING**  
> Last field-passed baseline: **V1.0-R5.7.41.3.4.10.11.2 FIELD PASS**  
> Science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`

## 本版核心

`.10.12` 正式開始 **Ice Optics Phase 2**，但只做 Native Microphysics Capability Audit 與 Mapping Eligibility Contract。

本版沒有建立任何假設性的：

- r_eff → Dmax
- IWP → Dmax
- temperature / RH / cloud fraction → Dmax
- habit rule
- roughness rule
- PSD rule

## 現有 GFS / CASE 真正提供的能力

### GFS native input

目前 native GRIB ingest 能看到：

- `ICMR`
- `CLWMR`
- `RWMR`
- `SNMR`
- `GRLE`
- `TCDC`
- `TMP`
- `RH`
- `HGT`

其中與 cloud-ice Phase 2 最直接相關的是 `ICMR`，但其物理語意是 bulk cloud ice mass mixing ratio，不是 Dmax，也不是 PSD。

### PhysicsCore deterministic derived evidence

由 ICMR + pressure + temperature + vertical geometry 可得到：

- IWC
- IWP proxy（在完整 vertical support 時數值單位可視為 kg/m²）
- native vertical completeness

以上仍然只是 mass / path / support 證據，不能單獨定義 particle size distribution。

### 目前缺少

- native Yang/Bi-compatible Dmax
- validated calibrated Dmax mapping
- native particle size bins
- ice particle number concentration
- sufficient PSD moments / PSD parameters
- validated calibrated PSD mapping
- validated habit resolution
- validated surface roughness resolution

## Phase 2 readiness state

```text
SCIENCE_BASELINE = R5.7.41.2_SHADOW_COT_AB_FROZEN
ICE_PHASE2_MODE = DIAGNOSTIC_READINESS_ONLY

NATIVE_ICE_MASS_INPUT_READY = true
NATIVE_THERMODYNAMIC_CONTEXT_READY = true
NATIVE_VERTICAL_PROFILE_SUPPORT = true
NATIVE_DMAX_AVAILABLE = false
CALIBRATED_DMAX_MAPPING_AVAILABLE = false
NATIVE_PSD_AVAILABLE = false
CALIBRATED_PSD_MAPPING_AVAILABLE = false
ICE_HABIT_RESOLUTION_READY = false
ICE_ROUGHNESS_RESOLUTION_READY = false

MICROPHYSICS_MAPPING_READY = false
SINGLE_PARTICLE_LUT_LOOKUP_ELIGIBLE = false
BULK_PSD_SYNTHESIS_ELIGIBLE = false
PRODUCTION_ICE_OPTICS_READY = false
physics_promotion_allowed = false
```

## TWS175 `.10.11.2` CASE replay

新 audit 已使用真正既有 FIELD PASS CASE 做離線 replay：

- GFS inventory：408 rows
- native voxels：96,876 rows
- native columns：2,691 rows
- positive IWP：213 rows
- Dmax：0 rows
- r_eff：0 rows
- resolved habit：0 rows
- resolved roughness：0 rows

結論：`INSUFFICIENT_MICROPHYSICS`。

這個結果與 `.10.11.2` FIELD PASS 的「213 positive-IWP、0 six-band ready」一致，現在只是把原因進一步結構化成正式 capability/mapping contract。

## Frozen science

完全不改：

- Formation = Sun → CloudBase
- Viewing = Cloud → Observer
- Twilight Glow independent
- 550 / 575 / 600 / 650 / 700 / 750 nm
- Canvas 0–40 / 40–100 km
- Corridor 100–350 km
- REZ 350–440 km
- Earth Shadow / Penumbra
- Production / Shadow COT
- CLWMR / ICMR existing threshold semantics
- Missing != Clear != Zero
- WINDY portable runtime decoupling

## CASE 新增輸出

- `ice_microphysics_native_input_capability_audit.csv`
- `ice_microphysics_phase2_mapping_eligibility.csv`
- `ice_microphysics_phase2_contract.json`

## 測試狀態

- working-tree full regression：**772 passed / 0 failed / 1 existing warning**
- targeted Phase 2 + Ice Optics regression：**25 passed**
- FIELD validation：**尚未執行 `.10.12` 新 CASE**

因此本版只能稱為 **IMPLEMENTATION / REGRESSION PASS**，不可提前稱 FIELD PASS。

## 下一步

優先進行 **Phase 2 Step 2 — authoritative size/PSD source capability survey**。

在找到可審核的來源前，不建立經驗 Dmax、habit、roughness、PSD 代理規則。
