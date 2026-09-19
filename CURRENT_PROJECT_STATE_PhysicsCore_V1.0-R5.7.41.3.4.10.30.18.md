# Taiwan Firecloud PhysicsCore — Current Project State

## 現行工程版本
`1.0.0-R5.7.41.3.4.10.30.18`

## Science baseline
`R5.7.41.2_SHADOW_COT_AB_FROZEN`

## Step 3Q.18 現行結論
Fu96-lineage primary solar parameterization 在 `0.700 μm` 有正式 spectral boundary。RRTMG Band 25 完全位於其短波側；RRTMG Band 24 則跨越該 boundary。

由於 Fu96-lineage co-albedo broad-band averaging 使用 `beta_lambda * solar irradiance` 權重，並保留 linear / logarithmic spectral moments後再混合，這個轉換一般不是只靠 compact final broad-band values 就能唯一逆轉。故：

- `FU96_PRIMARY_0P700UM_SPECTRAL_BOUNDARY_PINNED=True`
- `RRTMG_BAND25_WITHIN_SINGLE_FU96_PRIMARY_BAND_QUALIFIED=True`
- `RRTMG_BAND24_STRADDLES_FU96_PRIMARY_0P700UM_BOUNDARY_QUALIFIED=True`
- `RRTMG_BAND24_FINAL_TABLE_INVERSE_REAVERAGING_NONUNIQUE_QUALIFIED=True`
- `RRTMG_BAND24_FINAL_TABLE_INVERSE_REAVERAGING_UNIQUE=False`
- `FINAL_TABLE_INVERSE_IDENTIFICATION_ALLOWED=False`

## 尚未關閉的 blocker
1. Fu96 high-resolution ice-cloud pre-averaging spectral samples。
2. Historical Fu96 cloud pre-averaging generator。
3. Exact historical solar spectrum / discrete weights。
4. Deterministic RRTMG Band 24/25 reproduction。
5. Original AER v2.5 archive bytes/hash（次要於前四項，但仍屬 provenance 缺口）。

## 下一個有效開發方向
不得再以 final-table inverse fitting 作為主要路徑。只接受：
- authoritative high-resolution sample/generator recovery；或
- 由獨立 spectral optical dataset 建立逐波長 equivalent reconstruction，再用 archived Band24/25 final tables 做 like-for-like deterministic validation。
