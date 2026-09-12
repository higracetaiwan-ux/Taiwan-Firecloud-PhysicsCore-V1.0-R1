# Taiwan Firecloud PhysicsCore — Current Project State

Current candidate: **V1.0-R5.7.41.3.4.3**.

## Development strategy

Shadow Validation CASE 仍依實際天氣條件逐步收集，不為湊樣本放寬科學門檻，也不暫停工程完善。

目前 science baseline 繼續凍結：

`R5.7.41.2_SHADOW_COT_AB_FROZEN`

## R5.7.41.3.4.3 focus

DWD ICON secondary runtime hardening：

- 避免同一 run/lead 的 native QC/QI/T/P 在 13 個角度重複 decode；
- 歷史 run/lead 完整 QC/QI probe 全為 HTTP 404 時，後續角度使用 process-local negative cache；
- Missing 仍是 Missing，不變成 Clear/Zero；
- time-specific vertical geometry 每角度重新計算。

## CASE evidence

Historical DWD all-404 CASE：
- 108 fields / angle；
- 13 angles；
- 舊 audit = 1404 HTTP 404；
- 新 contract 將相同 process 的後續 12 angles suppress，network-attempt 上限由 1404 降到 108（all-404 pattern）。

## Verification

Working tree: **612/612 PASS**；trial fresh-extract: **612/612 PASS**；final candidate fresh-extract: **612/612 PASS**；1 個既有 pandas FutureWarning，非失敗。Exact final archive fresh-extract: **612/612 PASS**。Release Gate CLOSED。

## Next safe engineering target

在不改 science baseline 前提下，繼續 profile：

1. `TWILIGHT_GLOW_INDEPENDENT_BRANCH`；
2. `AGGREGATION_AND_MATRIX_BUILD`；
3. CASE export serialization。

優先找 deterministic cache / duplicate computation；不得以降低物理解析度、刪除六波段、合併 Formation/Viewing/Glow 來換速度。
