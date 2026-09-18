# Taiwan Firecloud PhysicsCore — Current Project State

## 現行版本
`1.0.0-R5.7.41.3.4.10.30.5`

## Science baseline
`R5.7.41.2_SHADOW_COT_AB_FROZEN`

## 現行 Step 3Q gate
`PASS_FAIL_CLOSED_POST_AVERAGED_ARCHIVE_BOUNDARY_QUALIFIED_EXACT_GENERATOR_UNRECOVERED`

## 已資格化
- Fu96/Fu-lineage solar-weighted linear/log coalbedo equation family
- Fu-lineage h-domain constraints：<0.700 µm 為 h=1；0.700–1.220 µm 為 h=2/3（lineage constraint，非 archived RRTM generator proof）
- RRTMG band 25 完全位於 h=1 domain
- RRTMG band 24 跨 0.700 µm boundary
- AER RRTM_SW public runtime archive 的 post-averaged table boundary

## 現在最重要 blocker
Public RRTM_SW source 只有 post-averaged Fu96 tables，未保存 Q. Fu high-resolution pre-averaging spectral tables 或 historical band-averaging generator。因此不可由 final tables 反推唯一 h/weights。

## 下一步
追 archived historical generator、preprocessor、private/high-resolution table lineage；只有 authoritative generator 或可重現 band 24/25 archived tables 的完整 provenance chain 被 recovered 後，才進 exact reproduction / Step 3R。
