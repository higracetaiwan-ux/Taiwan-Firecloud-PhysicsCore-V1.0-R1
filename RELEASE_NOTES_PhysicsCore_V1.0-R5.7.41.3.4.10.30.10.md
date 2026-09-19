# Taiwan Firecloud PhysicsCore — Release Notes

版本：`1.0.0-R5.7.41.3.4.10.30.10`  
名稱：**Step 3Q.10 — Official AER v2.5 Archive Publication-Chain Qualification**

## 本版變更
- 納入 AER 官方 RRTM_SW Code and Examples 所列 source archive filename：`aer_rrtm_sw_v2.5.tar.gz`。
- 納入 AER 官方 repo pinned `README.cvs_checkin_notes`：2004 public-release procedure 使用 `script_build_rrtm_sw.pl` 建立網站 source/example tar files，且 release build 必須使用正確 version number。
- 新增正式規則：**官方 archive filename + 官方 web tar-build procedure 可以證明 publication lineage，但不能取代 original archive bytes / hash。**
- external v2.5 mirror 仍可作 source-lineage evidence，但不得提升為 original AER tarball byte identity。
- `.10.30.9` 的 mirror import-time / historical CVS-time separation、runtime Kurucz low/high-resolution distinction、official runtime solar context 全部保留。
- Frozen science baseline 完全不變。

## Qualification state
`PASS_FAIL_CLOSED_V25_OFFICIAL_ARCHIVE_PUBLICATION_CHAIN_QUALIFIED_ORIGINAL_TARBALL_HASH_UNRECOVERED_PREAVERAGING_GENERATOR_UNRECOVERED`

## 仍 fail-close
- original AER v2.5 tarball bytes：未恢復
- original tarball provenance-qualified hash：未恢復
- external mirror byte identity：未證明
- historical pre-averaging generator：未恢復
- Q. Fu high-resolution pre-averaging tables：未恢復
- exact solar spectrum/grid/weights：未恢復
- Band 24 / 25 exact reproduction：未完成
- `EXACT_FU96_BAND_WEIGHTING_AVAILABLE=False`
- `TAU_ICE_PRODUCTION_ALLOWED=False`
- `PRODUCTION_ICE_OPTICS_READY=False`
- Step 3R：blocked

## Release artifact SHA256
- evidence: `5b059e87ff1ff9995a08f0ceee2921412db3af2612636b7cf5443d5a1aff6d7b`
- gate: `edbf59d61846af685cc954ae441859dfd285959ccb83239197d7021a837b5bcb`
- contract V1_10: `3d038fafee25d8b958ad70c948b36f57daf608dd6c38e1793e513bf7fd9673bc`
