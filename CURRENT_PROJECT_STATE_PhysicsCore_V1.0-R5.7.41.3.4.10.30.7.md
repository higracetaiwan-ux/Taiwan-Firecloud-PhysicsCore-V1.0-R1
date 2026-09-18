# Taiwan Firecloud PhysicsCore — Current Project State

版本：`1.0.0-R5.7.41.3.4.10.30.7`
Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`
目前步驟：Step 3Q.7 — Historical Public Release vs Current Archive Availability Boundary Qualification

## 現況
- RRTM_SW v2.4：2002 年有 historical public release 證據。
- RRTM_SW v2.5：2006 年文獻有實際使用證據。
- 現行 AER RRTMG_SW 公開 release archive：pre-v5 releases 目前不可得。
- 公開 RRTM_SW runtime source：只有 post-averaged Fu96 band tables / interpolation，沒有 historical pre-averaging generator。
- exact Fu96/RRTM generator：未恢復。
- band 24 / 25 exact reproduction：未執行。
- Production Ice Optics / tau_ice / physics promotion：全部禁止。

Qualification state：
`PASS_FAIL_CLOSED_HISTORICAL_PUBLIC_RELEASE_EXISTENCE_AND_CURRENT_ARCHIVE_BOUNDARY_QUALIFIED_EXACT_GENERATOR_UNRECOVERED`

下一個有效 blocker：尋找 archival Q. Fu high-resolution tables、AER historical cloud-table preprocessor、舊 distribution/build artifacts，或等價可直接重建 archived band-24/25 tables 的 authoritative generator。
