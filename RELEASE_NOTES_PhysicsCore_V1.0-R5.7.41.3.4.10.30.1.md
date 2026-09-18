# Release Notes — PhysicsCore V1.0-R5.7.41.3.4.10.30.1

## Step 3Q.1：Fu96/RRTMG Band-Weighting Semantic Narrowing

本版不是 Production Ice Optics promotion，而是 `.10.30` provenance blocker 的證據收斂。

### 新增證據
- Fu 2007 對 Fu96 lineage 的 solar-irradiance weighted band-average 說明。
- Yi et al. 2013 的 RRTMG SW band-integration 公式語義：`S(λ)` weighting、SSA scattering/extinction ratio、`g` scattering weighting。
- RRTMG band 24 / 25 boundaries pin。
- Baek & Bae 2018 作為 RRTMG spectral-band averaging 的獨立文獻交叉證據。

### 修正
`.10.30` 將 solar-flux weighting 與 extinction/scattering weighting 全部視為「不得假設」；本版將它精確化：
- solar-spectrum weighting 的**語義類別**已獲證據支持；
- SSA/g 的 cross-section weighting 公式亦可資格化；
- 但未 pin 的 historical solar spectrum / discrete weights 仍不得當作 exact RRTMG default Fu96 transform。

### 仍 fail-close
- historical pre-averaging sample set：未取得
- exact historical solar spectrum + discrete weights：未取得
- band 24 / 25 exact reproduction：未執行
- exact weighting：False
- SSA/g independent validation：False
- production tau_ice：False
- Production Ice Optics：False

Frozen Formation / Viewing / Twilight Glow、六波段、Canvas、Dynamic、Earth Shadow、COT 與 Missing≠Clear≠Zero 全部不變。
