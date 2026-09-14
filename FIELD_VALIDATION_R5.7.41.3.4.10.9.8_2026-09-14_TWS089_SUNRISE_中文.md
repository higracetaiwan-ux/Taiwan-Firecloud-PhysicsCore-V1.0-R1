# `.10.9.8` TWS089 2026-09-14 sunrise Field Validation

## 結論
`.10.9.8` 的 **HTTPS Connection Reuse = FIELD PASS**；但 **Cross-Release user-level cache scope 發現 app/worker contract defect**，因此該 release 不把 cache-scope 宣告為完整 Field PASS，缺陷由 `.10.9.9` 修正。

## Integrity
- Job: COMPLETED
- Analysis Integrity: 84 PASS / 1 NOT_APPLICABLE / 0 FAIL
- CASE Integrity: 38/38 PASS
- CAMS `CAMS_SPECTRAL_AOD_EXACT_REUSE_PROVENANCE`: PASS

## Runtime A/B（同 TWS089 sunrise）
| Stage | `.10.9.7` | `.10.9.8` | 差異 |
|---|---:|---:|---:|
| Worker | 639.155 s | 574.204 s | −64.950 s |
| Core | 602.000 s | 540.009 s | −61.991 s |
| DWD secondary prefetch | 158.752 s | 46.263 s | −112.489 s / −70.9% |
| CAMS prefetch | 173.194 s | 228.508 s | +55.314 s（provider latency variation） |
| All-angle Physics | 183.146 s | 178.148 s | −4.998 s |
| Timeline | 8.703 s | 7.592 s | −1.111 s |

DWD `.10.9.8` 仍下載 347 objects、約 436.7 MB，raw_cache_hit=0，因此 DWD 的 112 s 改善主要可歸因於 thread-local HTTPS Session keep-alive，而不是 persistent cache hit。

## Cache-scope defect
CASE `dwd_icon_request_audit.csv` 雖寫 `shared_cache_scope=USER_LEVEL_CROSS_RELEASE_EXACT_IDENTITY`，實際 `cache_file` 位於 `/.../.firecloud_state/provider_cache_shared/dwd_icon_raw/...`。原因是 app 無論使用者是否設定 state root，都會把 concrete `FIRECLOUD_STATE_DIR` 注入 worker；provider 因此誤判成 explicit override。此為 provenance/cache-placement defect，不改 science bytes。

## Science regression
`.10.9.7 ↔ .10.9.8` 共 138 個共同 artifacts，114 byte-identical。`v1_formation.csv`、`v1_photography_decision.csv`、`v1_red_light_reference_550_750nm.csv`、`v1_cloud_layers.csv`、`native_gfs_cloud_voxel_3d.csv`、`native_cloud_optical_blocking_voxel_3d.csv` 均 byte-identical。
