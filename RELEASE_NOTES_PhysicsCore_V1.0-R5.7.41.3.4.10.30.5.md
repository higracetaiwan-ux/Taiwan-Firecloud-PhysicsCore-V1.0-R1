# Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.30.5 Release Notes

## 名稱
Step 3Q.5 — RRTM_SW Post-Averaged Archive Boundary Qualification

## 核心變更
- 釘住 AER `RRTM_SW/src/cldprop.f` historical runtime archive，commit `b1253809ac88ae782964cd030cb202a380032d11`，blob SHA `8632f7d1940285665b62fdbb30c69861924251da`。
- 明確區分：public RRTM_SW runtime archive 保存的是已經 band-averaged 的 `EXTICE3/SSAICE3/ASYICE3/FDLICE3` tables 與 Dge interpolation，而不是 Q. Fu 提供的 high-resolution pre-averaging spectral tables / historical averaging generator。
- 釘住 ICEFLAG=3 的 46-node Dge runtime grid：5, 8, …, 140 µm（3 µm spacing）。
- 新增禁止規則：不得從 final broad-band tables 反解唯一 historical `h`、solar spectrum grid 或 discrete weights。

## 科學狀態
`PASS_FAIL_CLOSED_POST_AVERAGED_ARCHIVE_BOUNDARY_QUALIFIED_EXACT_GENERATOR_UNRECOVERED`

仍未 recovered：
- band 24 historical cross-0.7 µm mixing realization
- band 25 archived-generator identity
- historical pre-averaging spectral samples
- exact historical solar spectrum/grid/discrete weights
- band 24/25 exact numeric reproduction

Production gates 全部維持關閉。Science baseline 維持 `R5.7.41.2_SHADOW_COT_AB_FROZEN`。

## 驗證
- Targeted: 15/15 PASS
- Full regression: 945/945 PASS
- 1 個既有 pandas FutureWarning，0 failure
- FIELD CASE: pending
