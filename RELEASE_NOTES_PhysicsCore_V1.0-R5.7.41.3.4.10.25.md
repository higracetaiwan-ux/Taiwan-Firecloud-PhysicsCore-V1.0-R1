# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.25

## Step 3L — Yang/Bi Habit + Roughness Qualification

本版不啟用 production Ice Optics；目標是把 habit 與 roughness 從 hidden assumption 改成明確、可稽核的 qualification / uncertainty contract。

### Changes
- 凍結 Yang/Bi V2 inventory：9 habits、3 roughness states、189 Dmax、6 bands。
- 建立 Wyser solid-column lineage → Yang/Bi `single_column` model-family bridge。
- 明確保留 `exact_geometry_equivalence=false` 與 `GFS_NATIVE_HABIT_INFERENCE=false`。
- 對 9 habits 與三種 roughness 的 source-row optics 做 sensitivity characterization。
- 對 `single_column` 執行 `Rough000/Rough003/Rough050` PSD-weighted diagnostic ensemble。
- 新增 Step 3L evidence/gate/contract、Analysis Integrity、CASE archive handoff。

### Fail-close
- no runtime habit default
- no runtime roughness default
- no habit/roughness interpolation
- no production `tau_ice`
- no physics promotion

### Baseline
Latest formal FIELD baseline：`V1.0-R5.7.41.3.4.10.24.1 FIELD PASS`。
