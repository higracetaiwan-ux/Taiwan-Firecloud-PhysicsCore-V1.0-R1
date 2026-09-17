# Taiwan Firecloud PhysicsCore — Step 3K Stable Evidence Serialization Hotfix

版本：`1.0.0-R5.7.41.3.4.10.24.1`

## 目的
修正 `.10.24` TWS100 FIELD CASE 中 Step 3K evidence / contract 與 release static artifacts 在不同 runtime/platform 下出現約 `1e-16` 等級浮點 byte drift 的問題。

## Frozen boundary
- Science baseline 維持 `R5.7.41.2_SHADOW_COT_AB_FROZEN`。
- Step 3K science version 仍為 `R5.7.41.3.4.10.24`。
- Fu96、Wyser Eq.(5)/(6)、Step 3J Yang/Bi diagnostic bulk 計算全部不變。
- Formation / Viewing / Twilight Glow / production Ice runtime 全部不變。
- 不解鎖 habit、roughness、scientific bulk validation、`tau_ice` 或 production promotion。

## Hotfix
Step 3K evidence/output layer 使用 `11 significant digits` canonicalization。底層 scientific calculations 保留原始 double precision。

已知 FIELD platform variants 必須 canonicalize 為相同輸出：
- `1.22441956002415e-05` / `1.224419560031046e-05` → `1.22441956e-05`
- `0.26212710714149406` / `0.262127107141494` → `0.26212710714`
- `0.31216620726536515` / `0.31216620726536526` → `0.31216620727`

Contract 中相同 diagnostic numeric fields 先 canonicalize，再保存為 JSON number；不將數字改成字串。
