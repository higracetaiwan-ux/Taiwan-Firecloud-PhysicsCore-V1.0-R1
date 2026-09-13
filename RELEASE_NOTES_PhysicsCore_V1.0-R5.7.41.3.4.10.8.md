# Release Notes — V1.0-R5.7.41.3.4.10.8

## Viewing→Glow Molecular Context Handoff

本版是 runtime-only exact-reuse release。Main Viewing 已建立的 gas runtime context 內含 Glow 所需的 exact z/T/P numeric arrays；`.10.8` 直接 handoff 這些 arrays，避免 Glow 再次對 53k-row gas profile 做完整 pandas groupby/conversion。

### Fail-close

Shared handoff 必須覆蓋全部 exact gas routes 且每個 prepared gas context 都 `valid=True`。否則整體退回 `.10.2` independent molecular prep，保留 T/P-only Rayleigh readiness 與 HITRAN species readiness 的獨立性。

### Actual TWS091 benchmark

- 39 routes / 2691 profiles：全部 numeric/boundary metadata exact。
- molecular preparation median：3.537930 s → 0.115728 s（約 30.57×）。
- 此為 local same-input benchmark，Field gate 尚未關閉。

### Regression

- `.10.8` targeted + adjacent：12/12 PASS。
- Full working-tree：687/687 PASS，1 existing pandas FutureWarning。
- Science baseline remains `R5.7.41.2_SHADOW_COT_AB_FROZEN`.
