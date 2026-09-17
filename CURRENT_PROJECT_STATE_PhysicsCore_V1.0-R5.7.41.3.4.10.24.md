# Taiwan Firecloud PhysicsCore V1.0 — Current Project State

> Current development release: **V1.0-R5.7.41.3.4.10.24**  
> Latest formal FIELD baseline: **V1.0-R5.7.41.3.4.10.23.1 FIELD PASS**  
> Frozen science baseline: **R5.7.41.2_SHADOW_COT_AB_FROZEN**

## 本版定位

R5.7.41.3.4.10.24 = **Ice Optics Phase 2 Step 3K — Fu96 Independent Bulk Extinction Cross-Check**。

Step 3J 已能以 Wyser Eq.(6) PSD × Yang/Bi V2 diagnostic `C_ext` 計算六波段 `β_ext / k_ext`。Step 3K 新增一條不使用 Yang/Bi `C_ext` 的 reference chain：保留同一 Wyser number population，改用 Wyser Eq.(5) projected area + Fu (1996) geometric-optics `β≈2A_c`，用來獨立交叉檢查 bulk extinction。

## 主要結果

- 18-case reference matrix：PASS。
- Fu projected-area chain：numeric PASS。
- 最大 Fu unit-chain relative error：`1.2244195600241499e-05`。
- Step 3J Yang/Bi diagnostic `k_ext` 相對 Fu cross-check 差異：`0.26212710714149406` ～ `0.31216620726536515`。
- 253.16 K / 0.1 g m^-3：Fu reference `k_ext=48.83268509507885 m²/kg`；Step 3J 六波段約 `35.34–35.74 m²/kg`。
- mass-area-equivalent `Dge=51.5726471165019 µm`；solid-hex geometry `Dge=113.08468136924637 µm`；兩者不得互換。

## Gate

```text
FU96_INDEPENDENT_OPTICAL_CROSSCHECK_EXECUTED = true
FU96_PROJECTED_AREA_CHAIN_NUMERIC_PASS = true
FU96_DGE_DUAL_SEMANTICS_SEPARATED_PASS = true
FU96_BULK_DIFFERENCE_CHARACTERIZED = true

SCIENTIFIC_BULK_VALIDATION_PASS = false
BULK_YANG_BI_PSD_INTEGRATION_ELIGIBLE = false
TAU_ICE_PRODUCTION_ALLOWED = false
PRODUCTION_ICE_OPTICS_READY = false
physics_promotion_allowed = false
```

## 為何仍不 promotion

Fu96 reference 是獨立 optical-kernel cross-check，但不是與目前 Yang/Bi habit/roughness 完全 like-for-like 的 production reference。26–31% 的 material difference 反而再次顯示：Wyser population 與 Yang/Bi optical geometry 的 projected-area / shape / habit bridge 尚未完成。Eq.(6) independent external numeric corroboration、habit、roughness 也仍是 blockers。

## 下一步

先做 `.10.24 FIELD`，確認 Step 3K evidence/gate/contract 正確進 CASE 且 runtime `Dmax/habit/roughness/k_ext/tau_ice` 仍 fail-close。FIELD PASS 後再決定下一步優先處理 Yang/Bi habit/roughness qualification 或建立更 like-for-like 的 independent optical validation reference。
