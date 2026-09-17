# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.24

## Step 3K — Fu96 Independent Bulk Extinction Cross-Check

新增獨立 bulk optical cross-check。與 Step 3J 不同，本版 reference chain 不使用 Yang/Bi `C_ext`；它沿同一 Wyser number population 計算隨機取向 hex-column projected area，再採 Fu (1996) geometric-optics `β≈2A_c` 形成 reference `k_ext`。

18-case matrix 全部 numeric PASS。Step 3J 相對 Fu reference 的差異範圍約 26.2–31.2%。此結果證明 Step 3J 不只是 integrator 自我收斂，但不構成 production validation；shape / projected-area / habit / roughness 仍未等價。

特別新增 Dge dual-semantics guard：Wyser Eq.(6) population mass 所形成的 mass-area-equivalent Dge，不得與 solid-hex `rho*V` geometry Dge 互換。

Frozen Science baseline `R5.7.41.2_SHADOW_COT_AB_FROZEN` 不變。沒有啟用 production `k_ext` / `τ_ice` / Formation promotion。
