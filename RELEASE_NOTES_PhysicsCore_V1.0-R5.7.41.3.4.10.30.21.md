# Taiwan Firecloud PhysicsCore V1.0 — Release Notes

## R5.7.41.3.4.10.30.21

**Step 3Q.21 — Band25 Historical Source-Domain / Runtime-Weight Scope Qualification + CAMS Bounded Reattach Observation Window**

本版不修改 `R5.7.41.2_SHADOW_COT_AB_FROZEN`。

### Band25 provenance narrowing
新增：
- `firecloud/fu96_rrtmg_band25_historical_scope.py`
- `tools/verify_fu96_rrtmg_band25_historical_scope.py`
- `tests/test_r574134103021_band25_historical_scope_and_cams_bounded_reattach.py`

正式新增 gates：
- `FU96_LINEAGE_200_WAVELENGTH_SAMPLE_COUNT_QUALIFIED=True`
- `FU96_LINEAGE_SOLAR_PRIMARY_BAND_COUNT_QUALIFIED=True`
- `FU96_LINEAGE_EXACT_200_WAVELENGTH_NODE_GRID_RECOVERED=False`
- `RRTMG_FU96_RUNTIME_DGE_3UM_LINEAR_INTERPOLATION_PINNED=True`
- `RRTMG_RUNTIME_DGE_INTERPOLATION_IS_SPECTRAL_PREAVERAGING_REALIZATION=False`
- `RRTMG_BAND25_RUNTIME_GPOINT_REDUCTION_SCOPE_QUALIFIED=True`
- `RRTMG_BAND25_RUNTIME_RWGT_IS_CLOUD_PREAVERAGING_SOLAR_WEIGHT_VECTOR=False`
- `RRTMG_BAND25_RUNTIME_SFLUXREF_REDUCTION_PROVES_HISTORICAL_CLOUD_WEIGHTING=False`

這些資訊只縮小 historical reconstruction 搜尋範圍，不能解鎖 exact Band25 reproduction。

### CAMS bounded reattach observation window
`.10.30.20 FIELD PASS` 首次 FIELD exercise same-request-ID adaptive reattach；兩個 native 3-D aerosol roles 在 reattach 後仍 timeout，但 no fresh submit / fail-close 正確。

本版將 reattach-only 的等待時間與 initial provider deadline 分離：
- 210 s → 73.5 s default observation window
- 90 s → 31.5 s
- 小於 default window 的 initial deadline不增加
- env override：`FIRECLOUD_CAMS_DEFERRED_REATTACH_DEADLINE_SECONDS`
- override 也不得超過 initial deadline

保留：
- original ADS request ID
- `reattach_only=True`
- no fresh submit
- no duplicate ADS jobs
- timeout 後 Missing/fail-close
- timeout 後不做 adaptive subdivision 製造 duplicates

### Fail-close
所有 Production Ice Optics / Step3R gates 維持 False / BLOCKED；不以 runtime `rwgt`、`sfluxref`、3-µm Dge interpolation 或假定均勻 200-node grid 代替 historical cloud pre-averaging inputs。
