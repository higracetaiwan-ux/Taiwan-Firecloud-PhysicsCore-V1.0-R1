# Taiwan Firecloud PhysicsCore — Current Project State

版本：`1.0.0-R5.7.41.3.4.10.30.1.1`

狀態：**QA PASS / FIELD CASE pending**

## 本版目的

修正 Step 3Q.1 FIELD integrity state matcher regression。這是 integrity-only hotfix，不更動科學計算。

## Step 3Q.1 正式狀態

`PASS_FAIL_CLOSED_WEIGHTING_SEMANTIC_CLASS_QUALIFIED_EXACT_HISTORY_UNRESOLVED`

已資格化：solar-spectrum weighting semantic class；SSA 為 band-integrated scattering/extinction；g 為 scattering-weighted。

仍未資格化：historical exact Fu96/RRTMG solar spectrum、sample grid、discrete weights、band 24/25 exact reproduction。

因此 production gates 全部維持 false。
