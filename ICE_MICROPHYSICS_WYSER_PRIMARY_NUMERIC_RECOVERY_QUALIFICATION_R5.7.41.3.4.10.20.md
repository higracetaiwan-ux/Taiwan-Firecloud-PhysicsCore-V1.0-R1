# Taiwan Firecloud PhysicsCore — Ice Optics Phase 2 Step 3G

## 版本
`V1.0-R5.7.41.3.4.10.20`

名稱：**Primary Wyser Eq.(5)/(6) Numeric Recovery Audit + Synthetic Mass-Closure Harness Readiness**

## 目的
Step 3G 不宣告已取得 Wyser Eq.(5)/(6) 的 primary machine-readable numeric contract。
本階段把「primary numeric recovery 是否足以 promotion」本身變成 hard gate，並建立一個只可使用 synthetic/generic input 的 diagnostic mass-closure harness。

## Primary-source 結論
Wyser (1998) primary article 可直接確認：
- 所有粒子以 size-dependent aspect-ratio 的 hexagonal columns 表示；
- Eq.(5) 是 solid-column `L` 與 `D` 的連續 length-width relationship；
- Eq.(6) 描述 `m(L)=rho(L)V(L)`，primary prose 指定 `m` 為 grams、`L` 為 microns，適用 cold solid columns with `L/D>2`；
- 目前 publication HTML 中 Eq.(5)/(6) 仍以 equation image 呈現，而 Eq.(6) flattened machine extraction 不完整/損壞。

因此：**不能從目前 flat/OCR extraction 猜係數或指數。**

## Non-primary numeric lineage
後續文獻多次明確把 hex-column relation

`D = 2.5 L^0.6`

歸因給 Wyser / Wyser and Yang (1998)。Step 3G 將它保存為 `CORROBORATED_NONPRIMARY_NUMERIC_LINEAGE`，但不把它升格為 primary Eq.(5)。

## Dual-source numeric promotion policy
Scientific mass closure 前必須同時滿足：
1. primary-quality machine-verifiable Eq.(5) numeric representation；
2. primary-quality machine-verifiable Eq.(6) numeric representation；
3. independent transcription / reproduction PASS；
4. coefficients / exponents / units / coordinate conventions consistency PASS。

任一條件缺失都必須 fail-close。

## Synthetic diagnostic closure harness
新增 `diagnostic_mass_closure()`：
- caller 提供 `length_um / shape_weights / mass_g / iwc_g_m3`；
- 計算 `A=IWC / integral[m(L)phi(L)dL]`；
- 重建 `integral[m(L)A phi(L)dL]`；
- 回傳 relative error。

但此 harness 永遠標記：
- `diagnostic_only=true`
- `input_contract=SYNTHETIC_GENERIC_NOT_WYSER_SCIENTIFIC_VALIDATION`
- `scientific_mass_closure_pass=false`

因此 synthetic closure PASS 只證明數值流程/代數可用，不證明 Wyser Eq.(5)/(6) 或 PSD 科學正確。

## Gate
正式 qualification state：

`WYSER_PRIMARY_NUMERIC_RECOVERY_UNRESOLVED_CLOSURE_HARNESS_READY`

關鍵狀態：
- `WYSER_EQ5_PRIMARY_MACHINE_NUMERIC_RECOVERED=false`
- `WYSER_EQ6_PRIMARY_MACHINE_NUMERIC_RECOVERED=false`
- `INDEPENDENT_TRANSCRIPTION_REPRODUCTION_PASS=false`
- `EQ5_EQ6_UNIT_CONSISTENCY_PASS=false`
- `DIAGNOSTIC_MASS_CLOSURE_HARNESS_READY=true`
- `SCIENTIFIC_MASS_CLOSURE_EXECUTED=false`
- `ABSOLUTE_PSD_RECONSTRUCTION_EXECUTABLE=false`
- `PSD_MASS_CLOSURE_VALIDATION_PASS=false`
- `WYSER_L_TO_YANG_DMAX_COORDINATE_VALIDATED=false`
- `PRODUCTION_ICE_OPTICS_READY=false`
- `physics_promotion_allowed=false`

## 禁止事項
- 把 secondary `D=2.5L^0.6` 直接標成 primary Wyser Eq.(5)；
- 從 corrupt Eq.(6) flattened/OCR string 推導係數；
- 用其他 Pruppacher/Klett、Mitchell、CEPEX 等 mass-size law 替代 Wyser Eq.(6)；
- 把 synthetic harness PASS 當 scientific Wyser mass-closure PASS；
- 未完成 dual-source numeric promotion 就重建 absolute PSD；
- 未驗證幾何座標就把 Wyser `L` 當 Yang/Bi `Dmax`；
- production Ice Optics 提前 promotion。

## WINDY 意義
WINDY portable interface 可以繼續，但 production Ice Optics capability 必須保持 fail-close。Step 3G 的價值是先準備可重複的 closure 執行框架；等 primary Eq.(5)/(6) 真正 recovery 後，可直接進 scientific closure grid，而不必重新設計流程。
