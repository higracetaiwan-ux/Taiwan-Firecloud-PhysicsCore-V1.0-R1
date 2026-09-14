# Taiwan Firecloud PhysicsCore — Current Project State

Current release: **V1.0-R5.7.41.3.4.10.9.3 — Observer Near-field Cloud Environment Diagnostic**

Internal version: `1.0.0-R5.7.41.3.4.10.9.3`

Science baseline remains frozen at **`R5.7.41.2_SHADOW_COT_AB_FROZEN`**.

## 目前狀態

- `.10.8` Viewing→Glow Molecular Context Handoff：**FIELD PASS**。
- `.10.9` Viewing→Glow Gas Spectroscopy Cache Handoff：以 TWS095 performance + TWS106 telemetry 組合證據，**FIELD PASS**。
- `.10.9.1` Gas Cache Telemetry Hotfix：Field telemetry 成功，157,248 handoff hits、0 miss、0 uncached fallback。
- `.10.9.2` Shadow Collection Zero-target Integrity Hotfix：TWS106 舊 CASE 離線重算由 28 PASS / 4 FAIL 修正為 **32/32 PASS**；只修 audit semantics，不改 science。
- `.10.9.3` Observer Near-field Cloud Environment Diagnostic：**703/703 regression PASS / FIELD RETEST CANDIDATE**。

## TWS106 重要發現

2026-09-14 sunset，TWS106 高美濕地：

1. Formation 13 個核心角度均沒有 formed Canvas；`v1_viewing_summary` 因沒有 formed target 為空。
2. 使用者提供 17:07:49 實景顯示觀測點前方有廣泛低雲，屬重要 Ground Truth。
3. 舊 CASE 的 `forecast_raw.csv` 在 18:00 仍顯示 0–100 km coarse low-cloud evidence：
   - 40–100 km 中心線平均約 26.8%、最高 38%。
   - 40–100 km +5°側平均約 42.7%、最高 58%。
4. 同一 0–100 km 範圍，GFS native condensate cloud columns 沒有建立低雲幾何。
5. 因此不能把 `NO_CANVAS`、空 Viewing target 或 native column absence 解讀成 clear sky。

## `.10.9.3` 新增

CASE 新增：

- `v1_observer_nearfield_cloud_environment.csv`
- `v1_observer_nearfield_cloud_environment_summary.csv`

目的：即使沒有 formed Canvas target，也保存觀測者 0–100 km 的 exact-time coarse low/mid/high cloud-cover、visibility、RH、precipitation 與 native cloud-column relation。

硬規則：

- diagnostic only；
- `Missing != Clear != Zero`；
- coarse cloud cover 不得轉成 τ/COT；
- native no-column 只標 `NATIVE_NO_CLOUD_COLUMN_AT_THRESHOLD`，不得稱 clear；
- 不修改 Formation / Viewing / Glow / Photography Decision；
- 不需要 formed target 才能輸出 observer environment。

## 下一步

使用 `.10.9.3` 跑正式 Field CASE。需確認：

- 兩個 near-field diagnostic CSV 在 CASE 中存在；
- no-Canvas case 仍有 0–100 km observer environment rows；
- `OBSERVER_NEARFIELD_DIAGNOSTIC_ROLE_SEPARATION = PASS`；
- `tau_synthesis_allowed=False`；
- `formation_promotion_allowed=False`；
- TWS106 類型案例能保留 coarse/native mismatch；
- 原 Formation / Viewing / Glow science output 不 regression。
