# Ice Optics Phase 2 Step 3C — GFS v16 `rei` ↔ Yang/Bi Dmax Bridge Feasibility Audit

版本：`R5.7.41.3.4.10.16`  
Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`  
模式：`GFSV16_REI_DMAX_BRIDGE_FEASIBILITY_AUDIT_ONLY`

## 1. 結論

本階段**拒絕**直接的一對一 `GFDL rei → Yang/Bi Dmax` 轉換。

理由不是缺少一個比例常數，而是兩者的物理語義不同：

- GFDL v1/2019 `cloud_diagnosis` 的 `reiflag=2` source branch 計算 `rei`，其 source 註解標示為 **Wyser (1998)** 路徑；`rei` 是用來描述冰雲粒子群體的 bulk effective radius。
- Wyser (1998) 的 effective radius 建立在冰晶 population / PSD、hexagonal-column 幾何及 size-dependent aspect ratio 的假設上；論文本身指出非球形冰晶的 effective radius 並非唯一幾何尺寸。
- Yang/Bi authoritative single-particle database 的主要尺寸座標是 `maximum_dimension_um`，並且必須與 `habit + roughness` 一起使用。

因此以下 shortcut 均不合法：

- `Dmax = rei`
- `Dmax = 2 × rei`
- generalized/effective diameter 直接改名為 Dmax
- `reimin/reimax` 當作 Yang/Bi Dmax bounds

## 2. Public-source provenance 發現

公開 CCPP source 中存在需要保留的 provenance 不一致：

- `physics/MP/GFDL/module_gfdlmp_param.F90` 的 parameter comment 將 `reiflag=2` 標示為 Donner et al. (1997)，`reiflag=5` 標示為 Wyser (1998)。
- 但 `physics/MP/GFDL/v1_2019/gfdl_cloud_microphys_mod.F90` 的實際 `if (reiflag .eq. 2)` source branch 明確標示 `cloud ice (Wyser, 1998)`，且實作 `bw` / `rei` 公式。

PhysicsCore 在 Step 3C 不自行「修正」哪一份文件，而是正式記錄：

`REIFLAG2_DOCUMENTATION_SOURCE_LABEL_CONSISTENCY = MISMATCH`

在 NCEP operational production binary exact source revision 尚未 authoritative pin 之前，此 mismatch 保持為 mapping blocker。

## 3. 更合理的候選路徑

雖然直接 `rei → Dmax` 被拒絕，但找到一條較物理一致的候選：

`GFS qi / T / density → exact Wyser population/PSD → Dmax distribution → Yang/Bi single-particle optics → PSD-weighted bulk optics`

這條路徑的重點是：

- Yang/Bi 的 `Dmax` 保持原本單粒子尺寸語義；
- 不把 bulk effective radius 假裝成單顆粒子的 Dmax；
- 由 compatible PSD 對 Yang/Bi single-particle `Qext / ω0 / g / projected area / volume` 做 bulk integration；
- 最後可產生六波段 bulk ice optical properties，而不需在 runtime 製造虛假的單一 Dmax。

目前只標記：

`BULK_PSD_INTEGRATION_PATH_IDENTIFIED = true`

但：

`BULK_YANG_BI_PSD_INTEGRATION_ELIGIBLE = false`

## 4. 尚缺的資格

在 bulk integration 可執行前，必須再完成：

1. 精確重建 Wyser 使用的 PSD coefficients、size branches/bins、integration limits。
2. 精確重建 hexagonal-column size-dependent aspect-ratio law。
3. 解決 public source `reiflag=2` 文件／source label mismatch，或取得足以 pin operational semantic 的 authoritative provenance。
4. 驗證 Wyser hex-column geometry 與 Yang/Bi `solid column` / `hollow column` 等 habit 的兼容性；不得默認 solid column。
5. 處理 Yang/Bi `smooth / moderately rough / severely rough` 三種 roughness；GFS/Wyser 沒有直接 roughness forecast state。
6. 定義 bulk integration normalization、六波段輸出、有效 domain 與 Missing/fail-close 邊界。
7. 建立 uncertainty envelope。
8. 完成獨立 bulk-optics validation。
9. 最後另設 production promotion gate。

## 5. 本版 gate

正式 qualification state：

`DIRECT_DMAX_BRIDGE_REJECTED_BULK_PSD_PATH_IDENTIFIED_NOT_QUALIFIED`

關鍵狀態：

- `GFSV16_REIFLAG2_SOURCE_FORMULA_PINNED=true`
- `REIFLAG2_DOCUMENTATION_LABEL_CONSISTENT=false`
- `GFDL_REI_IS_BULK_EFFECTIVE_RADIUS=true`
- `YANG_BI_SIZE_AXIS_IS_MAXIMUM_DIMENSION=true`
- `DIRECT_REI_TO_DMAX_ONE_TO_ONE_ELIGIBLE=false`
- `BULK_PSD_INTEGRATION_PATH_IDENTIFIED=true`
- `WYSER_PSD_RECONSTRUCTION_PINNED=false`
- `YANG_BI_HABIT_BRIDGE_VALIDATED=false`
- `YANG_BI_ROUGHNESS_BRIDGE_VALIDATED=false`
- `BULK_YANG_BI_PSD_INTEGRATION_ELIGIBLE=false`
- `GFSV16_DMAX_MAPPING_ELIGIBLE=false`
- `PRODUCTION_ICE_OPTICS_READY=false`
- `physics_promotion_allowed=false`

## 6. 主要 evidence sources

- CCPP Physics GFDL v1 source：`physics/MP/GFDL/v1_2019/gfdl_cloud_microphys_mod.F90`，public source SHA `ad0304074e17a7b83be2f0fe016345b7f11be4ef`。
- CCPP GFDL parameter module：`physics/MP/GFDL/module_gfdlmp_param.F90`，public source SHA `c20e229466a69f5d5e1705bded8a7b20fbd3977e`。
- Wyser (1998), *The Effective Radius in Ice Clouds*, Journal of Climate, DOI `10.1175/1520-0442(1998)011<1793:TERIIC>2.0.CO;2`。
- Wyser & Yang (1998), *Average ice crystal size and bulk short-wave single-scattering properties of cirrus clouds*。
- Yang et al. authoritative single-scattering database / Yang et al. (2013) ice crystal library：尺寸座標為 particle maximum dimension，含九種 habits 與三種 roughness states。

## 7. Frozen Science

Step 3C 僅新增 research/evidence/qualification gate：

- 不更動 Formation；
- 不更動 Viewing；
- 不更動 Twilight Glow；
- 不更動 550/575/600/650/700/750 nm；
- 不更動 Canvas/Corridor/REZ；
- 不向目前 Ice runtime 填入 `rei` 或 Dmax；
- 不合成新的 `tau_ice`；
- 不允許 production promotion。
