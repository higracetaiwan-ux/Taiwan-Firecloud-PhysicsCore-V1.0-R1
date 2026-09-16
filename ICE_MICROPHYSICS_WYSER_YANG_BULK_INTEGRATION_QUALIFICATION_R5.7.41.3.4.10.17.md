# Taiwan Firecloud PhysicsCore — Ice Optics Phase 2 Step 3D

## 版本
`V1.0-R5.7.41.3.4.10.17`  
名稱：**Wyser PSD + Yang/Bi Habit Bulk-Integration Contract Qualification**

## 目的
本階段不建立 `r_eff → Dmax` 單值公式，也不啟用 production Ice Optics。
目標是把未來「GFS v16/Wyser 粒子族群 → Yang/Bi 單粒子 Dmax LUT → bulk six-band optics」
所需的 PSD、幾何、habit、roughness、積分與驗證條件分離成可稽核 contract。

## 已固定的核心
- Wyser mixed PSD：小粒子 Gamma branch，20 μm 以上為 power-law branch。
- 小粒子 Gamma 參數：`ν=3`、`λ=0.3 μm^-1`。
- branch join：在 `L=20 μm` 保持連續。
- 預設積分域：`L=10–1000 μm`。
- GFS v16 公開 GFDL v1 source 對應的 B(T,IWC) 控制式已固定。
- Wyser 粒子族群屬 hexagonal columns，aspect ratio 隨尺寸改變。
- Yang/Bi authoritative size axis：`maximum_dimension_um`，domain 2–10000 μm。
- Yang/Bi 具有 solid hexagonal column habit，可列為 family-level candidate，但尚未驗證為 Wyser exact geometry。
- Yang/Bi roughness 維持 smooth / moderate / severe 三狀態；目前不得靜默選一個。
- bulk integration 的數學 normalization 已固定：
  - `C_ext = Q_ext × A_proj`
  - `C_sca = ω0 × C_ext`
  - `β_ext = ∫ n(D) C_ext dD`
  - `β_sca = ∫ n(D) C_sca dD`
  - `ω_bulk = β_sca / β_ext`
  - `g_bulk = ∫ n C_sca g dD / β_sca`
  - `k_ext = β_ext / IWC`
  - `τ_ice = IWP × k_ext`
- 六波段仍完整保留：550/575/600/650/700/750 nm。

## 尚未解決的核心 blocker
1. Wyser absolute PSD number-density normalization 尚未形成可獨立重現的完整 contract。
2. Wyser size-dependent hex-column exact width/length law 尚未 primary-source pin。
3. Wyser `L` 與 Yang/Bi `Dmax` 的幾何座標橋接尚未驗證。
4. solid column habit 只有 family-level candidate，尚未完成 volume / projected-area / aspect-ratio 相容性驗證。
5. roughness 沒有 GFS runtime state；三狀態 uncertainty ensemble 仍需敏感度與 policy 驗證。
6. 尚未完成 independent bulk-optics validation。

## Gate
正式狀態：
`WYSER_PSD_CORE_PINNED_GEOMETRY_HABIT_ROUGHNESS_BLOCKED`

因此：
- `BULK_YANG_BI_PSD_INTEGRATION_ELIGIBLE=false`
- `GFSV16_DMAX_MAPPING_ELIGIBLE=false`
- `PRODUCTION_ICE_OPTICS_READY=false`
- `physics_promotion_allowed=false`

## 明確禁止
- `Wyser L` 靜默當成 Yang/Bi `Dmax`
- Wyser hex-column 靜默當成 Yang/Bi solid-column exact match
- 沒有 exact contract 就從 IWC 自行補 PSD amplitude
- 靜默固定單一 roughness
- independent validation 前合成 production bulk `tau_ice`
- 回到 `Dmax=rei` 或 `Dmax=2×rei`

## WINDY 意義
Step 3D 讓 WINDY 最終 Ice Optics 的方向更清楚：不要求 WINDY 自行猜 Dmax；
PhysicsCore 應先產出已驗證的 **bulk-integrated six-band optics / compact LUT**。
在本階段，WINDY production Ice Optics 仍必須保持 capability fail-close。
