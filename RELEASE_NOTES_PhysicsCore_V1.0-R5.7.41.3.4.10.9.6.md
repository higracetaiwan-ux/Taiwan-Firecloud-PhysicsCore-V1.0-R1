# Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.9.6 Release Notes

## GFS Native Near-field Source Attribution + Timeline Valid-Time Provenance

`.10.9.5` TWS106 Field CASE 已確認 hourly GFS valid-time alignment 生效，但 0–100 km native cloud 仍全零。本版不調 threshold、不造雲，而是把 source-level pressure evidence正式保存，讓後續能區分「GFS source exact zero」「below-threshold positive」「reconstruction loss」。

### 新增

- `v1_gfs_native_nearfield_source_levels.csv`
- `v1_gfs_native_nearfield_source_summary.csv`
- 3 個 GFS source-attribution Integrity checks

### 修正

Observer Environment Timeline 的 native snapshot time 改以 provider `gfs_valid_time_utc` 為準。先前同一 f004 state 被 13 個 angle time 重複標記成多個 native snapshots，雖不影響 Physics，但 provenance 不精確。本版新增 `native_provider_valid_time` / `native_time_basis` 與 Integrity gate。

### Timeline 擴展

T−60→T+30 改成 **T−180→T+60 / 5 min**，用於捕捉日落前短生命期低雲／積雲演變。仍只使用已取得 route forecast，不新增 API，不把 timeline 回灌 PhysicsCore。

### 科學規則

Frozen science baseline 仍為 `R5.7.41.2_SHADOW_COT_AB_FROZEN`，核心 Formation / Viewing / Glow / gas RT / COT / Red-Light / Photography Decision 不變。
