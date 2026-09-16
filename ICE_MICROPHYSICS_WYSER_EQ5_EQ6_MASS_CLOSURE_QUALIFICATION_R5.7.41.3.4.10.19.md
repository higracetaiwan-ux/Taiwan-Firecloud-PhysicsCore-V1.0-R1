# Ice Optics Phase 2 Step 3F — Exact Wyser Eq.(5)/(6) Geometry + Mass-Size / PSD Mass-Closure Qualification

## 版本
`V1.0-R5.7.41.3.4.10.19`

## 本階段結論
本階段確認兩種不同強度的證據，並刻意保持分離：

1. **Primary semantic evidence**：Wyser (1998) 原文清楚說明所有粒子採 size-dependent aspect ratio 的 hexagonal columns；Eq.(5) 定義 solid-column length `L` 與 width `D` 的連續關係；Eq.(6) 定義 `m(L)=rho(L)V(L)`，其中密度與體積都依 `L` 參數化，適用 cold solid columns、`L/D>2`，`m` 以 grams、`L` 以 microns。
2. **Strong corroborating lineage**：Yost et al. (2010) 明確把 `D=2.5 L^0.6` 歸因於 Wyser and Yang (1998)；後續大氣化學／微物理文獻也用相同歸因。

但是 Wyser (1998) primary HTML 中 Eq.(5)/(6) 仍是 equation image，Eq.(6) 的機器文字抽取失真。因此 PhysicsCore **不把二手文獻的 `D=2.5L^0.6` 提升成 primary Eq.(5) numeric contract，也不從損壞 OCR 猜 Eq.(6) 的係數或指數**。

## Gate
正式狀態：
`WYSER_GEOMETRY_LINEAGE_CORROBORATED_PRIMARY_MASS_SIZE_CLOSURE_BLOCKED`

- `WYSER_EQ5_GEOMETRY_LINEAGE_CORROBORATED=true`
- `WYSER_EQ5_PRIMARY_NUMERIC_EQUATION_PINNED=false`
- `WYSER_EQ6_MASS_SIZE_PRIMARY_NUMERIC_PINNED=false`
- `ABSOLUTE_PSD_RECONSTRUCTION_EXECUTABLE=false`
- `PSD_MASS_CLOSURE_VALIDATION_PASS=false`
- `WYSER_L_TO_YANG_DMAX_COORDINATE_VALIDATED=false`
- `BULK_YANG_BI_PSD_INTEGRATION_ELIGIBLE=false`
- `GFSV16_DMAX_MAPPING_ELIGIBLE=false`
- `PRODUCTION_ICE_OPTICS_READY=false`
- `physics_promotion_allowed=false`

## 禁止捷徑
- 不得把 `D=2.5L^0.6` 的 secondary lineage 宣告成已機器驗證的 primary Wyser Eq.(5)。
- 不得使用 Wyser Eq.(6) 損壞 OCR 字串建立 `m(L)`。
- 不得在 exact primary `m(L)` 未釘住前宣告 PSD mass closure。
- 不得把 Wyser `L` 靜默等同 Yang/Bi `maximum_dimension_um`。
- 不得執行 absolute PSD reconstruction、habit/roughness default 或 production bulk `tau_ice`。

## 下一個科學取得點
真正能讓 absolute PSD 往前的關鍵，不是更多 secondary citations，而是取得**可機器驗證的 primary-quality Eq.(5)/(6)**（例如出版社 PDF equation image 的人工雙重轉錄／作者原稿／可信 archival copy），並以獨立單位檢查與 mass-closure grid 驗證。
