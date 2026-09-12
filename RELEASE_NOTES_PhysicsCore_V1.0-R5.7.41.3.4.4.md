# Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.4

## Twilight Glow Observer-Cloud Provenance Cache Hardening

本版延續 R5.7.41.3.4.3，針對 Historical CASE 中 `TWILIGHT_GLOW_INDEPENDENT_BRANCH` 的高耗時做純工程最佳化，不改任何物理公式、權重、門檻或 Missing 語義。

### 問題定位

`build_twilight_glow_branch()` 對每個 Glow atmospheric volume，在 Viewing 已判定 `VIEW_CLOUD_OPTICS_PARTIAL` 後，會再呼叫 observer-cloud conflict provenance 診斷。舊版每個 volume 都會重複：

- 掃描同一 time / solar-angle / direction 的 cloud transect；
- 重建 `_exact_cot_map()`；
- 重建 target-optics truth map；
- 對同一 cloud blocker 重算 `_projected_support_interval()`。

以 13 個太陽角度、每角度 84 個 Glow volumes 的 CASE，可形成 1092 次 volume diagnostics，而相同 transect 的 cloud geometry 其實可安全重用。

### 修正

1. Cloud layers 先依 `time × solar_altitude_deg × direction_offset_deg` 建立 immutable group index。
2. `_exact_cot_map()` 在 Glow branch 只建一次。
3. target optical truth provenance map 在 Glow branch 只建一次。
4. `_projected_support_interval()` 依 transect + cloud-layer identity 做 shared runtime cache。
5. 所有 cache 都是 process-local、diagnostic-only，不寫回任何 COT、Formation、Viewing 或 Glow physical value。
6. 新增 Glow runtime cache telemetry：cloud group count、provenance call count、support-cache entry count。
7. 保留既有 `AGGREGATION_AND_MATRIX_BUILD` inclusive timer，另新增 `AGGREGATION_EXCLUDING_TWILIGHT_GLOW`，避免把 Glow 與 aggregation 誤判成兩個互相獨立的瓶頸。

### 科學契約不變

- `R5.7.41.2_SHADOW_COT_AB_FROZEN` 不變；
- 六波段 550/575/600/650/700/750 nm 不變；
- Earth Shadow / DirectSolarFraction 不變；
- Formation / Viewing / Twilight Glow 三分支仍完全分離；
- Shadow eligibility 不放寬；
- `DIRECT_EVIDENCE_CONFLICT` 保持 fail-closed；
- Missing ≠ Clear ≠ Zero；
- 不降低 Glow volume 空間解析度；
- 不刪除任何 Glow extinction / scattering export。

### Offline equivalence benchmark

使用 2026-09-04 TWS021 CASE 保存資料，取單一角度（84 Glow volumes）做 baseline vs 新版離線重播：

- baseline：7.743 s；
- R5.7.41.3.4.4：3.491 s；
- speedup：約 2.22×；
- elapsed reduction：約 54.9%；
- `detail` 與 `summary`：`assert_frame_equal(check_exact=True)` 完全一致。

此 benchmark 未包含 CASE 未保存的 Glow 內部 route-snapshot precipitation re-run，因此只用來驗證本次 observer-cloud provenance cache 的 deterministic 等價與局部效能，不宣稱整體 CASE 一定等比例加速。

## Verification

- Working-tree regression: **616/616 PASS**
- Trial fresh-extract regression: **616/616 PASS**
- Existing pandas FutureWarning: 1 (non-failure)

- Final candidate fresh-extract regression: **616/616 PASS**

- Exact final archive fresh-extract regression: **616/616 PASS**

Release Gate: CLOSED.
