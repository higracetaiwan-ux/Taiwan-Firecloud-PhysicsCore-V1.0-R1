# Taiwan Firecloud PhysicsCore — Current Project State

## V1.0-R5.7.41.3.3

本版為 Historical Replay Empty Cloud-Volume Guard Hotfix。

### Field trigger
2026-08-30 歷史回測三次在約 376 秒後失敗，trace 固定落在 Twilight Glow 使用的 `build_viewing_spectral_extinction()` → `_cloud_expected_tau()`：`KeyError: 'direction_offset_deg'`。

CAMS 最後 worker `AEROSOL_SCATTERING_COLUMN_PROPERTIES` 已 COMPLETED，因此這不是 CAMS timeout；真正原因是歷史 replay 的 cloud-layer table 在特定分支為 headerless empty/malformed DataFrame，而舊程式未做 schema guard。

### 修正
- None/empty/malformed cloud volume → `VIEW_CLOUD_VOLUME_UNRESOLVED`。
- cloud tau / total transmission保持 Missing，analysis worker 不 crash。
- schema 完整但 route 真正無 blocker → `VIEW_CLOUD_PATH_CLEAR`，避免把真晴空誤降級。
- route grouping 對缺欄位 fail-safe。

### Science baseline
`R5.7.41.2_SHADOW_COT_AB_FROZEN`

### 不改動
Production/Shadow COT semantics、Formation、Viewing RT 公式、Twilight Glow science、Photography、六波段、太陽角度、Canvas/blocker 與 Missing 規則均不改。

### Historical replay note
2026-08-30 距目前仍在近期歷史窗內；本次失敗不能解讀為「API 無法回查」。修正版部署後應重新執行；若部署重啟保留 provider cache 可復用，若雲端 instance 重建清除 cache，則 provider 可能需要重新抓取。

### Release Gate
Working-tree regression：598/598 PASS；FULL-CLEAN fresh-extract regression：598/598 PASS；1 個既有 pandas FutureWarning，非失敗；Release Gate：CLOSED。
