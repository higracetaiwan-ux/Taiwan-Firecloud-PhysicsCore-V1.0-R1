# Taiwan Firecloud PhysicsCore V1.0 — R5.7.41.3.4.10.30.15

## Step 3Q.15 — Official AER RRTM_SW→RRTMG_SW Fu96 Final-Table Continuity Qualification

本版只強化 provenance，不修改 frozen science baseline `R5.7.41.2_SHADOW_COT_AB_FROZEN`。

新增 AER 官方跨世代證據：2004 RRTM_SW v2.5 `cldprop.f` 與 2007 RRTMG_SW `rrtmg_sw_cldprop.f90` 的 `EXTICE3 / SSAICE3 / ASYICE3 / FDLICE3` 完整比較，56/56 arrays、2576/2576 numeric values 完全一致。

此結果只證明 final band-table continuity；不等於 pre-averaging spectral samples、historical generator、exact solar weighting 或 original `aer_rrtm_sw_v2.5.tar.gz` hash 已恢復。Production Ice Optics 與 Step 3R 繼續 fail-close。

QA：Step3Q 48/48 PASS；full regression 975/975 PASS；0 failures；1 existing pandas FutureWarning。
