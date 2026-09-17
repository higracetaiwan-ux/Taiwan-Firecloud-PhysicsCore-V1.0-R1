# ICE MICROPHYSICS — Wyser → Yang/Bi Dmax Coordinate Qualification

Version: `R5.7.41.3.4.10.21`  
Science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`  
Status: **QA-qualified / FIELD validation pending**

## 1. Qualification scope

Step 3H 僅判定 **size-coordinate identity**，並刻意將它與 shape / projected area / volume-mass / habit / roughness / bulk optics / production promotion 分離。

本版允許：

```text
Wyser L_um == Yang/Bi maximum_dimension_um
```

但這個等號只代表「兩者都使用 particle maximum dimension 作為尺寸座標」，**不代表兩套 solid-column 幾何或光學等價**。

## 2. Wyser side

Wyser (1998) 將 nonspherical ice-particle size distribution 定義在 maximum dimension / length `L`，並用 width `D` 描述形狀。已恢復的 Eq.(5) 在診斷點均有 `D <= L`，因此 axial `L` 為 maximum dimension。

## 3. Yang/Bi V2 size coordinate

Authoritative Ice LUT manifest 已凍結：

- dataset: `TAMU_ICE_SINGLE_SCATTERING_V2`
- source version: `Yang2013_Bi2017_V2`
- primary size coordinate: `maximum_dimension_um`
- `single_column` 為正式 habit。

因此 Yang/Bi side 的 size axis 是 particle maximum dimension。

## 4. Exact single-column geometry source-row reproduction

為避免把文獻文字轉錄誤差帶入 runtime，本版不單靠 PDF 顯示的係數；直接使用 bundled LUT 中由 authoritative source `volume/projected_area` rowwise 推出的 `effective_diameter_um = 1.5V/A` 做 independent machine reproduction。

Pinned geometry:

```text
a = 0.35 L                 L < 100 µm
a = 3.48 sqrt(L)           L >= 100 µm
width = 2a
```

Regular hexagonal-column diagnostic geometry:

```text
V = (3 sqrt(3) / 2) a^2 L
A_proj(random convex) = [3 sqrt(3) a^2 + 6 a L] / 4
De = 1.5 V / A_proj
```

Source reproduction result:

- source rows: **189**
- max relative `De` error using `3.48`: **5.8372782357736544e-07**
- max relative `De` error using alternative `0.348`: **0.89729574585075733**
- source-row geometry reproduction: **PASS**

因此，對本專案實際凍結的 Yang/Bi V2 source，`3.48` 由 source-row geometry 直接支持；`0.348` 不得取代它。

## 5. Shape compatibility result

即使 size coordinate identity 通過，Wyser Eq.(5) 與 Yang/Bi V2 single-column width law 在診斷點仍不相同：

- max relative width difference: **0.29999999999999999**
- solid-column shape compatibility: **BLOCKED**
- projected-area compatibility: **BLOCKED**
- volume/mass compatibility: **BLOCKED**

因此不能因為 `L == Dmax` 就直接把 Wyser PSD population 當成 Yang/Bi single-column population 做 production bulk optics。

## 6. Remaining blockers

- independent exact numeric corroboration for Wyser Eq.(6): pending
- scientific mass closure: not executed
- Wyser↔Yang shape/projected-area/volume-mass bridge: not validated
- Yang/Bi habit bridge: not validated
- roughness policy: not validated
- independent bulk six-band optics validation: not completed
- GFSv16 Dmax mapping: not eligible
- Production Ice Optics: not ready

## 7. Frozen Science

Formation / Viewing / Twilight Glow、六波段、Canvas/Corridor/REZ、Earth Shadow、Production/Shadow COT 與 Missing≠Clear≠Zero 全部不變。
