# Release Notes — V1.0-R5.7.41.3.4.10.9

## Viewing→Glow Gas Spectroscopy Cache Handoff

本版是 runtime-only exact-reuse release。Main Viewing 自 `.10.4` 起已用 content-scoped spectroscopy memo 快取 `_sigma_fast()` 的 O2/H2O/O3 六波段 cross section，但 Twilight Glow Volume Assembly 仍會再次計算相同 T/P state。`.10.9` 將 Main Viewing 已建立的 `gas_sigma_cache` 與 exact route 的 LUT content signature 直接 handoff 給 Glow gas-species path decomposition。

### Exact cache contract

沿用 `.10.4`，不建立第二套 key：

`LUT content signature + gas + wavelength + exact T + exact P`

命中時只重用同一個 sigma；每段 `sigma × number_density × path_length`、O2→H2O→O3 與六波段累加順序保持原樣。

### Fail-close / fallback

若 shared sigma cache 不存在，或該 exact gas route 沒有 LUT signature，Glow 完整走既有 `_sigma_fast()` 路徑，不猜測、不跨 LUT 重用。

### Actual TWS091 benchmark

2026-09-14 sunrise `.10.8` CASE，同一輸入、1092 Glow volumes：

- Main Viewing 預先 cache：約 450 entries
- Glow 完成後：約 11,394 entries
- gas-species path output differences：0/1092
- legacy：約 2.844 s
- shared cache handoff：約 1.073 s
- local speedup：約 2.65×

此為 local same-input benchmark，正式 Field gate 尚未關閉。

### Regression / science freeze

- `.10.9` targeted + adjacent：27/27 PASS。
- Full working-tree：691/691 PASS。
- 相對 `.10.8`：80 個 `firecloud/*.py` 中 78 個 byte-identical；功能變動只在 `twilight_glow.py`，另 `__init__.py` 更新版本號。
- `gas_rt.py`、Formation、Viewing decision、Spectral RT、COT、Earth Shadow、Photography 未修改。
- Science baseline remains `R5.7.41.2_SHADOW_COT_AB_FROZEN`.
