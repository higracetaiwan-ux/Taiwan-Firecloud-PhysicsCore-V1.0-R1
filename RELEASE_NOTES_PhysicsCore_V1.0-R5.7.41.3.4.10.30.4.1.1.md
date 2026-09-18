# Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.30.4.1.1

## Provenance Packaging Hotfix

本版只修正 Step 3Q.4 release artifact 的版本 provenance：上一版 `.10.30.4.1` 的 `release_artifacts/ice_microphysics_fu96_rrtmg_band_weighting_provenance_contract.json` 仍標記 `physicscore_version=...10.30.4`，而 FIELD runtime 正確輸出 `...10.30.4.1`，造成 CASE ↔ release contract 無法 byte-exact。

`.10.30.4.1.1` 將 release contract 的 `physicscore_version` 對齊實際程式版本。`STEP3Q_VERSION` 維持 `R5.7.41.3.4.10.30.4`，因為 Step 3Q.4 科學內容沒有任何變更。

Science baseline、Formation / Viewing / Twilight Glow、六波段、Canvas / Corridor / REZ、Earth Shadow、COT、ice-optics production gates 全部不變。

Production Ice Optics 仍 fail-close；不得因本 hotfix 啟用 `tau_ice` 或 physics promotion。
