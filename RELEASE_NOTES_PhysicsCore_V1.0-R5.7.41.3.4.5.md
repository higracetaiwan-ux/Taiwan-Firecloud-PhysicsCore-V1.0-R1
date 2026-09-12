# Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.5

## Viewing→Glow Observer-Cloud Provenance Handoff + Shared Runtime Context

本版延續 R5.7.41.3.4.4，繼續處理 Twilight Glow / Viewing 在 Cloud→Observer path 上的重複計算。這是純工程最佳化，不修改任何火燒雲物理公式、權重、門檻或 Missing 語義。

### 問題定位

Viewing 已經逐 target 追蹤 observer-cloud blocker geometry、cloud optical state 與 unresolved/conflict blocker；Glow 在取得 `VIEW_CLOUD_OPTICS_PARTIAL` 後，舊流程仍會逐 atmospheric volume 再追一次同一組 cloud blockers，只為恢復 conflict provenance。

此外 Viewing 與 Glow 也會各自建立重複的 route groups、gas contexts、COT/truth maps 與 projected-support geometry cache。

### 修正

1. Viewing 在原 blocker traversal 中同步留下 Glow 所需的 cloud conflict provenance。
2. Glow 優先讀取 Viewing handoff，不再重追相同 observer-cloud geometry。
3. 新增 shared runtime context，共用 grouped routes、prepared HITRAN gas contexts、exact COT map、target truth map 與 support cache。
4. Runtime context 僅對 exact same in-memory source DataFrame objects reuse；來源物件不同必須 rebuild。
5. 舊 CASE / external input 若沒有 handoff columns，仍保留 R5.7.41.3.4.4 fallback retrace，維持相容性。
6. 新增 telemetry：handoff hits、fallback provenance calls、context reused、gas context source。

### 科學契約不變

- `R5.7.41.2_SHADOW_COT_AB_FROZEN` 不變；
- Production COT / Shadow candidate semantics 不變；
- Shadow eligibility 不放寬；
- Earth Shadow / finite solar disk / DirectSolarFraction 不變；
- Formation / Viewing / Twilight Glow 三分支物理不變；
- 六波段 550/575/600/650/700/750 nm 不變；
- `DIRECT_EVIDENCE_CONFLICT` 保持 fail-closed；
- Missing ≠ Clear ≠ Zero；
- 不降低 route / volume 空間解析度。

### Offline exact-equivalence benchmark

2026-09-04 TWS021 CASE 保存資料、單一 −2°角度、84 Glow volumes：

- R5.7.41.3.4.4：3.9605 s；
- R5.7.41.3.4.5：2.0351 s；
- speedup：約 1.946×；
- elapsed reduction：約 48.6%；
- legacy cloud provenance retrace：84 → 0；
- Viewing provenance handoff hits：0 → 84；
- `detail` / `summary` exact DataFrame equality：PASS。

此 benchmark 只代表被測 handoff/shared-context path，不宣稱 full online CASE 必然等比例加速。

## Verification

- Targeted regression: **26/26 PASS**
- Working-tree regression: **619/619 PASS**
- Existing pandas FutureWarning: 1 (non-failure)
- Trial fresh-extract regression: **619/619 PASS**
- Exact final archive fresh-extract regression: **619/619 PASS**

Release Gate: **CLOSED**.
