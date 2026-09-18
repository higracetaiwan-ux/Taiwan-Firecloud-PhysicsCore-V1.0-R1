# Taiwan Firecloud PhysicsCore V1.0 — R5.7.41.3.4.10.30.2 Release Notes

## 名稱
Step 3Q.2 — Fu96/RRTMG Historical Averaging-Semantics Qualification

## 目的
修正 Step 3Q.1 中「後期 RRTMG-band integration formula」與「歷史 Fu96 default-table 生成語義」可能被誤視為同一件事的風險。

## 本版新增/凍結
- Fu96 historical coalbedo/SSA broad-band averaging：solar-weighted，且依吸收強弱使用 linear / logarithmic averaging 的混合語義。
- Yi2013 RRTMG-band integration：保留為後期 RRTMG-band ice-optics 的獨立語義證據，不得當作 archived default Fu96 tables 的歷史生成器。
- RRTMG_SW v4.0 以前 runtime solar source：Kurucz，TSI 1368.22 W m-2，僅作 historical runtime context。
- band 24/25 band-integrated solar irradiance totals可 pin，但不得由 band total 反推 within-band discrete weights。
- 未證明 runtime Kurucz spectrum/grid 與 Q. Fu high-resolution table generation 使用的 exact spectrum/grid/weights 相同。

## 維持 fail-close
- exact historical Fu96 band-specific linear/log mixing realization：未取得。
- pre-averaging Fu spectral samples：未取得。
- exact historical solar spectrum / sample grid / discrete weights：未取得。
- band 24/25 exact reproduction：未執行。
- `EXACT_FU96_BAND_WEIGHTING_AVAILABLE=False`
- independent SSA/g validation：False
- full six-band like-for-like validation：False
- `TAU_ICE_PRODUCTION_ALLOWED=False`
- `PRODUCTION_ICE_OPTICS_READY=False`
- physics promotion：False

Science baseline `R5.7.41.2_SHADOW_COT_AB_FROZEN` 不變。
