# Release Notes — V1.0-R5.7.41.3.4.10.9.3

## Observer Near-field Cloud Environment Diagnostic

本版因 TWS106 2026-09-14 sunset Ground Truth 發現而新增：當 Formation 沒有 Canvas target 時，舊流程會使 Viewing target-dependent tables 合理為空，但 CASE 因此無法完整描述「觀測點本身及前方其實有很多低雲」的 observer environment。

### 新增 CASE artifacts

- `v1_observer_nearfield_cloud_environment.csv`
- `v1_observer_nearfield_cloud_environment_summary.csv`

### 科學邊界

本功能是 diagnostic-only：

- coarse low-cloud cover 不會被轉換成 τ/COT；
- 不把 RH/CF 造雲光學厚度；
- native no-column 不等於 clear；
- 不改 Formation；
- 不建立 Viewing target；
- 不改 Glow；
- 不改 Photography Decision。

### TWS106 proxy re-evaluation

以舊 CASE 18:00 hourly route rows + 0° native cloud columns 重建新 diagnostic：

- 45 個 0–100 km route points；
- native low-cloud geometry point count = 0；
- +5° Extended >40–100 km coarse low cloud mean = 42.7%，max = 58%；
- center Extended >40–100 km mean = 26.8%，max = 38%；
- 對應狀態：`COARSE_LOW_CLOUD_PRESENT_NATIVE_3D_NOT_RECONSTRUCTED`。

這只表示 coarse/native evidence mismatch，不自動判斷哪一個 provider 為真，也不合成 blocker τ。

### 包含 `.10.9.2`

同時包含 Shadow Collection zero-target Integrity hotfix：物理上合法的 no-Canvas / zero-target cohort，空 semantic-migration table 不再被誤判為 production switch / promotion。TWS106 舊 CASE離線重算後 CASE Integrity = 32/32 PASS。
