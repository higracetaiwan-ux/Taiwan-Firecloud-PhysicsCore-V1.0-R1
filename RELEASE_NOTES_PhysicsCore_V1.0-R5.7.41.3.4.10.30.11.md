# Taiwan Firecloud PhysicsCore — Release Notes

版本：`1.0.0-R5.7.41.3.4.10.30.11`  
名稱：**Step 3Q.11 — Official AER Historical Source-Tree CVS-Normalized Equivalence Qualification**

## 本版變更
- 直接 pin AER 官方 `AER-RC/RRTM_SW` 歷史 repository 中的 2004 source history：
  - `src/cldprop.f`：commit `356609ea083f9684dc83a56e3f5c96515cb25b19`，2004-04-15 18:42:10 UTC。
  - `src/taumoldis.f`：commit `a43212334fd726dec8d69203be0c7d50fd9ce1b0`，2004-04-15 18:50:57 UTC。
- 對 external v2.5 mirror import commit `040d18018f553faeeae625fd4ef73d50ba0436fb` 做 full-file comparison：
  - `cldprop.f`：2080 vs 2080 lines；raw 差異僅 CVS keyword collapse/expansion；canonical CVS normalization 後完整一致。
  - `taumoldis.f`：2054 vs 2054 lines；canonical CVS normalization 後完整一致；mirror expansion 保留 revision 2.5 / 2004-04-15 18:50:57。
- 新增正式規則：**critical historical source-tree equivalence 可以 qualified，但不得提升為 original tarball byte identity 或 original archive hash。**
- `.10.30.10` 的 official archive publication-chain qualification 全部保留。
- 修正 examples archive metadata 副檔名為官方頁面所列 `aer_rrtm_sw_examples_v2.5.tar.gz`。
- Frozen science baseline 完全不變。

## Qualification state
`PASS_FAIL_CLOSED_V25_OFFICIAL_SOURCE_TREE_CVS_NORMALIZED_EQUIVALENCE_QUALIFIED_ORIGINAL_TARBALL_HASH_UNRECOVERED_PREAVERAGING_GENERATOR_UNRECOVERED`

## 仍 fail-close
- original `aer_rrtm_sw_v2.5.tar.gz` bytes：未恢復
- original tarball provenance-qualified hash：未恢復
- external repository/archive 與 original AER tarball byte identity：未證明
- historical pre-averaging generator：未恢復
- Q. Fu high-resolution pre-averaging tables：未恢復
- exact solar spectrum/grid/weights：未恢復
- Band 24 / 25 exact reproduction：未完成
- `EXACT_FU96_BAND_WEIGHTING_AVAILABLE=False`
- `TAU_ICE_PRODUCTION_ALLOWED=False`
- `PRODUCTION_ICE_OPTICS_READY=False`
- Step 3R：blocked

## Release artifact SHA256
- evidence: `625e582660536f40a944f48e2a1888a14df5fc82157402dc1bb9f9a6836faf6b`
- gate: `470a7a84af79d84a4b17f4c64a1928949714dba1904a403e5124a19f4cf09bb9`
- contract V1_11: `1d2bf6bdd5653ba8801902f15aac0491f3ecf46d5fcaa1a5048791f2252fc068`
