# Taiwan Firecloud PhysicsCore — Current Project State

Current candidate: **V1.0-R5.7.41.3.4.5**.

## Development strategy

Shadow Validation CASE 持續依實際天氣慢慢收集；工程開發不必等待 cohort 補齊。所有 Ground Truth 僅驗證，不反向改寫 Forecast truth。

Science baseline 持續凍結：

`R5.7.41.2_SHADOW_COT_AB_FROZEN`

## R5.7.41.3.4.5 focus

Viewing→Glow observer-cloud provenance handoff + shared runtime context：

- Viewing 已做過的 blocker geometry 不再由 Glow 重跑；
- conflict provenance 在 same pass 保留並 handoff；
- Viewing / Glow 共用 route groups、gas contexts、COT/truth lookup 與 projected-support cache；
- exact source-object identity guard 防止 stale/cross-run cache；
- legacy/external input 無 handoff 時仍安全 fallback；
- Missing / conflict / physical values 不變。

## Verification evidence

H004 / TWS021 單角度 84-volume offline equivalence replay：3.9605 s → 2.0351 s，約 1.946×；detail / summary exact match；legacy provenance retrace 84 → 0。

## Next safe engineering targets

1. 依 `AGGREGATION_EXCLUDING_TWILIGHT_GLOW` 確認 full CASE 剩餘 aggregation 成本；
2. CASE export serialization 針對大型 DataFrame 做實測，不以膨脹 CASE 體積換速度；
3. profile Glow precipitation / aerosol observer-path 是否仍有可安全共用幾何；
4. Shadow CASE 繼續隨天氣收集，不為工程進度強跑不適合的事件。

## Verification

Targeted regression **26/26 PASS**；working tree **619/619 PASS**；trial fresh-extract **619/619 PASS**；exact final archive fresh-extract **619/619 PASS**；1 個既有 pandas FutureWarning，非失敗；Release Gate CLOSED。
