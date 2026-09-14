# Ice Optics Portable WINDY Decoupling Spec — R5.7.41.3.4.10.10.1

## 目的

本版把 Ice Cloud Spectral Optics 的部署責任正式拆開：

- **PhysicsCore**：authoring / authoritative LUT build / calibration / validation / release certification。
- **WINDY Firecloud Observer**：consumer；匯入已發布的 portable package 後在瀏覽器/外掛本地執行。
- WINDY runtime **不得依賴正在執行的 PhysicsCore、Python、Streamlit 或 PhysicsCore API**。

這是 deployment contract 變更，不是 Frozen Physics science 變更。

## Portable contract

Contract：`FIRECLOUD_ICE_OPTICS_PORTABLE_V1`

Ice science contract：`FIRECLOUD_ICE_OPTICS_V1`

固定六波段：`550/575/600/650/700/750 nm`。

Runtime lookup 規則：

- wavelength：runtime 不插值；LUT 已預先正規化為六波段。
- effective radius：只允許同一 `ice_habit + surface_roughness` 內線性插值。
- habit：禁止插值。
- roughness：禁止插值。
- LUT domain 外：禁止 extrapolation，必須 Missing/fail-close。

光學公式：

`tau_ice(lambda) = IWP [kg/m²] × k_ext(lambda) [m²/kg]`

`T_ice(lambda) = exp(-tau_ice(lambda))`

## WINDY standalone package

有 calibrated LUT 時，PhysicsCore builder 產生：

- `manifest.json`
- `contract.json`
- `ice_optics_lut_v1.csv`
- `ice_optics_lut_v1.json`
- `windy/iceOpticsEvaluator.mjs`
- `windy/iceOpticsEvaluator.ts`
- `validation/reference_vectors.json`
- `validation/validatePackage.mjs`
- `README_WINDY.md`
- `source/source_manifest.json`（若提供）

Package manifest 對每個檔案保存 `SHA256` 與 byte size。

## Cross-language gate

PhysicsCore 以 Python reference evaluator 建立 deterministic validation vectors；WINDY-side dependency-free ES module 必須通過相同 vectors。

驗證向量只做 **software arithmetic/interpolation parity**，不是 climatology，也不是 habit/reff 科學校準資料。

Release 前可執行：

`node validation/validatePackage.mjs`

## Missing semantics

Frozen：`Missing != Clear != Zero`。

positive IWP 若缺任何一項：

- complete native vertical support
- calibrated effective radius
- calibrated/assigned ice habit
- calibrated/assigned roughness
- matching LUT domain

則 spectral ice tau 必須 Missing。

禁止：RH / Cloud Fraction / 季節經驗 / unlabelled fixed reff / unlabelled fixed habit 補造 tau。

## 與 `.10.10` CASE WINDY summary 的關係

`.10.10` 已輸出的 `v1_windy_ice_optics_summary.csv` / JSON 繼續保留，作 PhysicsCore Field / A-B / debugging evidence。

但 **它們不再是 WINDY 未來 runtime 的必要資料來源**。正式 runtime contract 是 portable LUT package。

## Frozen science isolation

`.10.10.1` 不修改：Formation、Viewing、Viewing spectral、Twilight Glow、Gas RT、Cloud Optics、Production/Shadow COT、Red-Light、Photography Decision、Earth Shadow、Dynamic Corridor/REZ、CLWMR/ICMR threshold。
