# `.10.12` Native Microphysics Capability Audit — TWS175 FIELD CASE Replay

## Replay source

既有 FIELD PASS：

`V1.0-R5.7.41.3.4.10.11.2 / TWS175 / 2026-09-17 sunrise`

本 replay **沒有重跑天氣模型，也沒有修改舊 CASE**；只用 `.10.12` 新 audit code 讀取舊 CASE 內已封存的 native evidence。

## Native GRIB evidence

`gfs_grib_message_inventory.csv`：408 rows。

實際 shortName：

`CLWMR, ICMR, RWMR, SNMR, GRLE, TCDC, TMP, RH, HGT`

這證明 current GFS ingest 的 bulk hydrometeor / thermodynamic / vertical inputs 確實存在，但 inventory 中沒有 Dmax、effective radius、particle number concentration、PSD bin、habit 或 surface roughness。

## Derived / runtime evidence

- native cloud voxels：96,876
- native cloud columns：2,691
- Ice Optics runtime：2,691
- positive IWP：213
- Dmax non-null：0
- r_eff non-null：0
- resolved habit：0
- resolved roughness：0

## Eligibility result

```text
NATIVE_ICE_MASS_INPUT_READY=true
NATIVE_THERMODYNAMIC_CONTEXT_READY=true
NATIVE_VERTICAL_PROFILE_SUPPORT=true
NATIVE_DMAX_AVAILABLE=false
CALIBRATED_DMAX_MAPPING_AVAILABLE=false
NATIVE_PSD_AVAILABLE=false
CALIBRATED_PSD_MAPPING_AVAILABLE=false
ICE_HABIT_RESOLUTION_READY=false
ICE_ROUGHNESS_RESOLUTION_READY=false
MICROPHYSICS_MAPPING_READY=false
SINGLE_PARTICLE_LUT_LOOKUP_ELIGIBLE=false
BULK_PSD_SYNTHESIS_ELIGIBLE=false
PRODUCTION_ICE_OPTICS_READY=false
physics_promotion_allowed=false
eligibility_state=INSUFFICIENT_MICROPHYSICS
```

## 結論

`.10.12` Step 1B 的 fail-close 判定與真正 FIELD CASE 相符：

**現在有 ICMR / IWC / IWP，但沒有可合法轉換為 Yang/Bi Dmax / PSD 的 native or calibrated evidence。**

因此不得先建立 r_eff→Dmax、IWP→Dmax、固定 habit 或固定 roughness 規則。
