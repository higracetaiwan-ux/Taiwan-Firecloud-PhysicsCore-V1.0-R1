# Ice Optics Phase 2 Step 3B — GFS v16 Exact Scheme Pinning

版本：`R5.7.41.3.4.10.15`

## 結論

目前能從公開、可重現的官方/社群 UFS/CCPP 證據把 GFS v16 微物理契約釘到以下層級：

- operational family：GFDL Cloud Microphysics。
- public reproduction family：CCPP `physics/MP/GFDL/v1_2019/`。
- GFS_v16 CCPP emulation namelist：`reiflag=2`。
- `reiflag=2` source semantic：cloud-ice effective radius (`rei`)，不是 Yang/Bi `maximum_dimension_um`。
- public parameter defaults：`reimin=10 µm`、`reimax=150 µm`，只屬 effective-radius bounds。

尚未完成：

- NCEP production binary exact source commit / build provenance。
- effective-radius → Yang/Bi Dmax 的 habit/PSD/mass-size semantic bridge。
- habit / surface roughness resolution。
- independent mapping validation。

因此本版只做 evidence pinning，不執行任何 Dmax/PSD reconstruction；`physics_promotion_allowed=false`。

## 重要版本隔離

公開 CCPP source tree 將 GFDL `v1_2019` 與 `v3_2022` 分開。GFDL MP v3 / SHiELD 的 PSD 公式不得替代 GFS v16 的 v1/2019 路徑。

## Frozen Science

仍為 `R5.7.41.2_SHADOW_COT_AB_FROZEN`，Formation / Viewing / Twilight Glow / 六波段 / Canvas / Corridor / REZ / Earth Shadow / Production-Shadow COT / Missing≠Clear≠Zero 全部不變。
