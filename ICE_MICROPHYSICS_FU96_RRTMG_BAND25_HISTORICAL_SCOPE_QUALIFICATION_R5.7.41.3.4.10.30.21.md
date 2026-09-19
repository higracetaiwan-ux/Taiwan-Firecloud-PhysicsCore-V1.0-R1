# Step 3Q.21 — Band25 Historical Source-Domain / Runtime-Weight Scope Qualification

## 已資格化
1. Fu96 lineage：single-scattering source calculations 使用 200 wavelength samples，並分為六個 solar primary bands，以 solar irradiance 參與 band averaging。
2. AER RRTMG_SW runtime `iceflag=3`：Dge 5–140 µm，3 µm table spacing，runtime 使用 linear interpolation。
3. AER RRTMG_SW Band25 current g-point reduction：`rwgt` 用於 molecular/Rayleigh coefficient reduction；`sfluxrefo` 被累加成 runtime `sfluxref`。

## 不得推論
- 200 samples ≠ exact 200 wavelength node coordinates。
- 3 µm Dge interpolation ≠ wavelength-domain spectral pre-averaging interpolation。
- runtime `rwgt` ≠ historical Fu96 cloud-table solar/discrete weight vector。
- runtime `sfluxref` reduction ≠ historical cloud table generator。

## 結論
Band25 remaining blocker 已縮小，但 exact historical intra-band realization 尚未 recover。所有 production gates 保持 fail-close。
