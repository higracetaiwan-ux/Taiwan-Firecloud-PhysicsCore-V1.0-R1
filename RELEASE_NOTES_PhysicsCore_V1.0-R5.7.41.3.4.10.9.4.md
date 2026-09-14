# Release Notes — V1.0-R5.7.41.3.4.10.9.4

## Observer Environment Timeline Diagnostic

本版只增加 observer-environment diagnostic time alignment，不改 frozen science。

### 新增

1. `v1_observer_environment_timeline.csv`
2. `v1_observer_environment_timeline_summary.csv`
3. 預設 T−60 → T+30、每 5 分鐘。
4. 延用既有 route linear interpolation；不新增 API request。
5. Native 3D 僅可掛接 ±180 秒內既有 snapshot，禁止 native 時間插值。
6. −6°後標 `POST_MINUS6_DIAGNOSTIC_ONLY`。
7. 4 個新的 Analysis Integrity checks。

### TWS106 離線證據

`.10.9.3` Field CASE 重算：855 point rows / 171 summary rows。可直接對齊 17:07→18:29 使用者實景；同時維持 `tau_synthesis_allowed=False`、`formation_promotion_allowed=False`、`native_temporal_interpolation_allowed=False`。

### Science

Science baseline remains `R5.7.41.2_SHADOW_COT_AB_FROZEN`。

### Verification

- working-tree regression: 709/709 PASS
- fresh-extract regression: 709/709 PASS
- FULL-CLEAN contamination: 0
