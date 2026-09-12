# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.8

## Viewing Path Geometry Runtime Optimization Phase 1

本版延續 R5.7.41.3.4.7.1，不修改凍結科學基線 `R5.7.41.2_SHADOW_COT_AB_FROZEN`。

### 為何改
R5.7.41.3.4.7.1 的 TWS106 Field CASE 已把 Viewing+Photography 130.925 s 拆解完成，最大單一 component 為 `build_viewing_path_geometry()` 56.920 s，超過 six-band Viewing extinction 的 40.711 s。

### 改動
- 新增 per-transect immutable numeric geometry plan。
- support interval / CF-continuity neighbour 預計算。
- target blocker selection 改用 array mask。
- 17-point LOS sample reuse：同一次 samples 同時做 cloud-volume intersection 與 crossing-position interpolation。
- 保留 unusual-schema fail-safe fallback。

### 科學不變
不改 Formation、Viewing semantics、CF occupancy rule、Earth Shadow、COT、六波段、Glow、Photography decision 或任何閾值。

### 驗證
- Targeted viewing/runtime tests：19/19 PASS。
- Working-tree full regression：638/638 PASS。
- TWS106 geometry exact-equivalence：1131 rows × 25 columns，0 differences。
- `.3.4.6 ↔ .3.4.7.1` 10 份核心 science CSV：byte-for-byte exact-equivalent。

### Field 狀態
此版為 Field-Test Candidate。必須在 Streamlit Cloud 重新跑 TWS106 後，才能關閉 geometry optimization milestone。
