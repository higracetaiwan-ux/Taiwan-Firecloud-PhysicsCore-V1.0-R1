# Observer Near-field Cloud Environment Diagnostic Spec — R5.7.41.3.4.10.9.3

## 1. 問題

Formation = NO_CANVAS 只代表沒有合格的火燒雲 Formation target，不代表觀測者附近天空無雲。舊 target-dependent Viewing tables 在 no-Canvas 時合理為空，但因此缺少 observer environment evidence。

## 2. 目的

建立 target-independent observer environment diagnostic，在 0–100 km 保存已有 provider evidence，讓 CASE 可表達：

- 近場／前方低雲存在；
- coarse cloud-cover 與 native 3D cloud geometry 不一致；
- Viewing target 不存在，但 observer environment 仍可能很差。

## 3. 輸入

只使用既有資料：

- exact-time route snapshots；
- `cloud_cover_low/mid/high`；
- visibility；
- RH2m；
- precipitation；
- GFS native cloud columns。

不新增 API request。

## 4. 距離域

- Near Observer：0–10 km
- Primary diagnostic：>10–40 km
- Extended diagnostic：>40–100 km

Point table 同時保留 frozen Canvas domain role：0–40 Primary、>40–100 Extended。

## 5. Native semantics

`NATIVE_NO_CLOUD_COLUMN_AT_THRESHOLD` 只代表 native condensate reconstruction 在目前 threshold 下沒有 cloud column；不得翻譯成 clear sky。

## 6. Coarse/native relation

主要狀態：

- `COARSE_AND_NATIVE_LOW_CLOUD`
- `COARSE_LOW_CLOUD_NATIVE_NO_COLUMN_AT_THRESHOLD`
- `COARSE_LOW_CLOUD_NATIVE_UNAVAILABLE`
- `COARSE_LOW_CLOUD_NATIVE_GEOMETRY_NOT_LOW`
- `NATIVE_LOW_CLOUD_COARSE_EXACT_ZERO`
- `COARSE_LOW_CLOUD_MISSING`

## 7. 禁止事項

- `tau_synthesis_allowed=False`
- `formation_promotion_allowed=False`
- `viewing_target_required=False`
- 不改 Formation / Viewing / Glow / Photography Decision
- 不用 coarse CF/RH 補造 τ/COT

## 8. CASE artifacts

### Point table

`v1_observer_nearfield_cloud_environment.csv`

### Summary

`v1_observer_nearfield_cloud_environment_summary.csv`

## 9. Integrity

新增：

- `OBSERVER_NEARFIELD_CLOUD_ENVIRONMENT_PRESENT`
- `OBSERVER_NEARFIELD_DIAGNOSTIC_ROLE_SEPARATION`
- `OBSERVER_NEARFIELD_CLOUD_ENVIRONMENT_SUMMARY`

## 10. TWS106 Ground Truth 意義

2026-09-14 17:07:49 實景顯示觀測點前方廣泛低雲。舊 CASE 18:00 coarse forecast 在 40–100 km 亦有 20–58% low-cloud evidence，但 native 3D 0–100 km 沒有低雲 geometry。此案例用於驗證 diagnostic evidence preservation，不用來反向改寫 forecast 或 Formation。
