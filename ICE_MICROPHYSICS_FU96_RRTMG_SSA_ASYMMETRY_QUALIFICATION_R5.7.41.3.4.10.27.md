# Step 3N — Fu96/RRTMG Independent Bulk-band SSA + Asymmetry Qualification

## 目的
建立與 Yang/Bi authoritative LUT 分離的冰雲 SSA / asymmetry (`g`) 參考來源鏈，並明確固定 RRTMG broad-band 與 PhysicsCore 六個單色波段之間的語義邊界。

## 來源鏈
- Fu (1996)：solar cirrus extinction / single-scattering albedo / asymmetry parameterization。
- RRTMG SW `ICEFLAG=3`：使用 Fu (1996) high-resolution tables 的 band-averaged `ssaice3` / `asyice3`。
- External implementation pin：GEOS-Chem `GeosRad/rrtmg_sw_init.F90`，commit `a4551f9442183bb572b23e9c2d362e2d34420d3a`，blob SHA `0ccf597d6aa3d6ed40ec592560e3ed94b653ef32`。

## 光譜語義
- RRTMG band 25：16000–22650 cm⁻¹（約 441.5–625 nm），只可作為 550/575/600 nm 的「包含其波長之 broad-band reference」。
- RRTMG band 24：12850–16000 cm⁻¹（約 625–778.2 nm），只可作為 650/700/750 nm 的「包含其波長之 broad-band reference」。
- 禁止把同一 broad-band `ssaice3` / `asyice3` 值複製後改稱六個 monochromatic truth。

## Step 3N gate
已確認：independent bulk-band SSA reference available、independent bulk-band asymmetry reference available、broad-band mapping semantics pass。

仍封鎖：independent SSA numerical validation、independent asymmetry numerical validation、exact six-band like-for-like optical validation、`tau_ice` production、Production Ice Optics、physics promotion。

## Frozen Science
Formation / Viewing / Twilight Glow、六波段 production contract、Canvas、Dynamic Corridor/REZ、Missing≠Clear≠Zero、runtime habit/roughness fail-close 全部不變。
