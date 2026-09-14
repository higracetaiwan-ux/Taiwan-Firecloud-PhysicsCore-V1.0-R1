# Taiwan Firecloud PhysicsCore — Current Project State

Current release: **V1.0-R5.7.41.3.4.10.9.4 — Observer Environment Timeline Diagnostic**

Internal version: `1.0.0-R5.7.41.3.4.10.9.4`

Science baseline remains frozen at **`R5.7.41.2_SHADOW_COT_AB_FROZEN`**.

## 已完成 Field gate

- `.10.8` Viewing→Glow Molecular Context Handoff：FIELD PASS。
- `.10.9` Gas Spectroscopy Cache Handoff：FIELD PASS。
- `.10.9.2` zero-target Integrity hotfix：TWS106 舊 CASE 離線重算 32/32 PASS。
- `.10.9.3` Observer Near-field Cloud Environment Diagnostic：TWS106 正式 CASE **FIELD PASS**；point 585 rows、summary 117 rows、CASE Integrity 34/34 PASS。

## `.10.9.4` 目的

把 observer-environment evidence 從 0°→−6°事件角度表擴成獨立時間軸：

- T−60 → T+30 min；
- 5 min 間隔；
- 0–100 km；
- 使用既有 hourly route forecast；
- native 3D 不做時間插值，只能掛接 ±180 s 內既有 snapshot；
- −6°後僅 `POST_MINUS6_DIAGNOSTIC_ONLY`，不擴張 PhysicsCore science window。

## TWS106 Ground Truth

目前使用者提供的實景時間：

- 高美 17:07:49：前方廣泛低雲；
- 彰化附近 17:52:09：厚廣低層雲場；
- 高美 18:02:00：地平線低雲帶，橙紅光從雲隙穿出；
- 高美 18:15:52：低雲遮擋持續；
- 高美 18:26:05：低雲帶，上方強橙黃 Glow；
- 彰化附近 18:26:31：廣泛破碎低雲；
- 高美 18:29:03 / 18:29:54：Strong Glow + Low-cloud obstruction。

影像只作 Ground Truth observer-environment evidence；不反推精確距離/雲底，不反向修改 forecast 或 Formation。

## `.10.9.4` TWS106 離線結果

以 `.10.9.3` CASE 的 `forecast_raw + native_gfs_cloud_columns + event_time_contract`：

- timeline：855 rows；
- summary：171 rows；
- Analysis Integrity 新增四項：全部 PASS；
- 17:05（對 17:07 圖）：中心 0–10 km low cloud mean 1.67%、10–40 km 4.01%、40–100 km 35.03%；
- 17:50（對 17:52 彰化圖）：中心 0–10 km 1.67%、10–40 km 4.14%、40–100 km 28.28%；+5° 40–100 km 39.96%；
- 18:00：中心 40–100 km mean 26.90%；+5° mean 42.66%；native matched，但仍無 low-cloud column；
- 18:15：中心 40–100 km 29.61%；+5° 42.28%；
- 18:25：中心 40–100 km 31.41%；+5° 42.03%；
- 18:30：已超過 −6° core endpoint，標 `POST_MINUS6_DIAGNOSTIC_ONLY`；中心 40–100 km 32.32%、+5° 41.91%，native time unmatched。

## 目前狀態

**709/709 regression PASS / FIELD RETEST CANDIDATE**。

下一步：用 `.10.9.4` 正式跑 TWS106 CASE，確認兩個 timeline CSV 入 CASE、4 個 timeline Integrity checks PASS、原 science outputs 不 regression。

## Release gate

- FULL-CLEAN entries: 796
- cache/pyc contamination: 0
- fresh-extract regression: 709/709 PASS
