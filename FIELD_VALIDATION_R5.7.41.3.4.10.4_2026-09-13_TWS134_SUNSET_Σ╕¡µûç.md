# R5.7.41.3.4.10.4 Field Validation — 2026-09-13 TWS134 日落

## 結論

**`.3.4.10.4 Viewing / Glow Gas Spectroscopy State Memo = FIELD PASS`**。

但本次 `.10.3 → .10.4` 並非固定 provider snapshot 的 byte-identical replay；Field 判定需同時看 live runtime 與同輸入離線 A/B。

## Integrity

- Analysis Integrity：**72/72 PASS**
- CASE Integrity：**32/32 PASS**

## Live runtime gate

同為 TWS134 / 2026-09-13 sunset：

- `TWILIGHT_GLOW_COMPONENT_OBSERVER_SPECTRAL_EXTINCTION`
  - `.10.3`：**8.532848 s**
  - `.10.4`：**6.642360 s**
  - 改善：**−22.2%**
- Twilight Glow total：25.573171 → **23.363876 s**
- Observer Precipitation：5.463031 → **5.270388 s**（維持 `.10.3` 改善）

## Provider snapshot 差異

`.10.3` 與 `.10.4` 執行期間 CAMS operational cycle 已更新：

- `.10.3`：CAMS `2026-09-12 12Z / lead 21h`
- `.10.4`：CAMS `2026-09-13 00Z / lead 9h`

GFS 兩次皆為 `2026-09-13 06Z / f003`；DWD 兩次皆使用 lead 4h，但 Open-Meteo / CAMS 均為 current-run evidence。

因此兩 CASE 的部分 spectral / Formation / Viewing / Glow science CSV 會隨 provider evidence 更新而改變，不能把 `.10.3 ↔ .10.4` byte-level 差異解讀為 memo science regression，也不能要求 67/67 `v1_*.csv` 完全一致。

## 同一 `.10.4` 輸入的 exact A/B

使用 `.10.4` CASE 的同一批 1092 Glow targets、相同 cloud/aerosol/gas evidence，比較 spectroscopy memo ON / OFF：

- memo ON full observer spectral：**約 2.50 s**
- memo OFF full observer spectral：**約 3.82 s**
- local speedup：約 **1.53×**
- DataFrame：**`check_exact=True`**
- memo entries：4752

這證明 `.10.4` 的 runtime memo 本身不改科學輸出；live Field 又觀察到 8.533 → 6.642 s 的 component 降幅，因此 `.10.4` 可正式 FIELD PASS。

## 下一步

`.10.4` 後，Glow observer spectral 仍是單一最大 component，但內部 profiling 顯示大量成本已移到 pandas route slicing / cloud-row materialization。先移除純 runtime 的 per-target aerosol/gas route slicing，再做下一個 Field gate；不先更動 cloud/gas physics。
