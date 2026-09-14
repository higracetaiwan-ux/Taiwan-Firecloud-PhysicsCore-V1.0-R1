# Observer Environment Timeline Diagnostic Spec — R5.7.41.3.4.10.9.4

## 1. 背景

`.10.9.3` 已證明 NO_CANVAS 時仍可保存 0–100 km observer-environment evidence，但原表的時間仍跟隨 PhysicsCore 0°→−6°事件角度，只涵蓋約 18:00→18:26。TWS106 Ground Truth 另外包含 17:07、17:52 以及 18:29 實景，因此需要一條不改 PhysicsCore 的診斷時間軸。

## 2. 目的

新增 event-relative Observer Environment Timeline：

- 預設範圍：T−60 分鐘 → T+30 分鐘；
- 間隔：5 分鐘；
- 距離：0–100 km；
- 只用既有 `forecast_raw` / hourly route data；
- 不新增 provider request；
- 不將 T+−6°後資料重新送入 Formation / Viewing / Glow。

## 3. Coarse forecast 時間處理

沿用既有 `interpolate_route_at_time()`：

`OPENMETEO_ROUTE_LINEAR_INTERPOLATION_EXISTING_CONTRACT`

時間內插只是 observer-environment diagnostic evidence，不產生新的光學量。

## 4. Native 3D 時間處理

Native cloud columns **禁止時間插值**。

只允許將已存在的 native snapshot 掛到 timeline target，條件：

- 同 direction / distance；
- 最近既有 native snapshot；
- `|Δt| <= 180 s`。

輸出：

- `native_reference_time`
- `native_time_delta_seconds`
- `native_time_match_state`
- `native_reference_solar_altitude_deg`

若無相近 snapshot，標：

`NO_NATIVE_SAMPLE_WITHIN_TIME_TOLERANCE`

不得把它翻成 clear。

## 5. Physics window role

- `PRE_CORE_EVENT_DIAGNOSTIC`
- `CORE_0_TO_MINUS6_TIME_RANGE`
- `POST_MINUS6_DIAGNOSTIC_ONLY`

`POST_MINUS6_DIAGNOSTIC_ONLY` 只是觀測環境證據；不代表 PhysicsCore 新增 −6°以下火燒雲計算。

## 6. 距離帶

- `NEAR_OBSERVER_0_10KM`
- `PRIMARY_GT10_40KM`
- `EXTENDED_GT40_100KM`

## 7. 硬規則

- `tau_synthesis_allowed=False`
- `formation_promotion_allowed=False`
- `viewing_target_required=False`
- `native_temporal_interpolation_allowed=False`
- coarse CF/RH 不得補造 τ/COT
- native no-column / native time unmatched 不得翻成 clear
- 不改 Formation / Viewing / Glow / Photography Decision

## 8. CASE artifacts

- `v1_observer_environment_timeline.csv`
- `v1_observer_environment_timeline_summary.csv`

## 9. Integrity

新增：

- `OBSERVER_ENVIRONMENT_TIMELINE_PRESENT`
- `OBSERVER_ENVIRONMENT_TIMELINE_ROLE_SEPARATION`
- `OBSERVER_ENVIRONMENT_TIMELINE_WINDOW_CONTRACT`
- `OBSERVER_ENVIRONMENT_TIMELINE_SUMMARY`

## 10. TWS106 驗證目的

`.10.9.3` CASE 離線套用本 diagnostic：

- point rows：855
- summary rows：171
- native time matched point rows：270
- native time unmatched point rows：585

此 timeline 可將 17:07→18:29 的 Ground Truth 圖像對到最近 5 分鐘診斷時刻，但單視角影像仍不得反推精確雲距離或雲底高度。
