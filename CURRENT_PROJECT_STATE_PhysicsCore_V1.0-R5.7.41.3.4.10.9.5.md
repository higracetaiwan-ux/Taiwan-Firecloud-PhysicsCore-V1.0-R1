# Taiwan Firecloud PhysicsCore — Current Project State

Current release candidate: **V1.0-R5.7.41.3.4.10.9.5 — GFS Hourly Native Valid-Time Alignment Hotfix**

Internal version: `1.0.0-R5.7.41.3.4.10.9.5`

Science baseline remains frozen at **`R5.7.41.2_SHADOW_COT_AB_FROZEN`**.

## 已完成 Field baseline

- `.10.9 = FIELD PASS`
- `.10.9.3 = FIELD PASS + TWS111 CROSS-SITE PASS`
- `.10.9.4 Observer Environment Timeline Diagnostic = FIELD PASS`

## TWS106 / TWS111 Ground Truth 問題

兩站實景皆證明 2026-09-14 sunset 前後有廣泛低雲；但 `.10.9.3/.10.9.4` 0–100 km native GFS cloud geometry 為空。深入追查後發現，在判斷 condensate threshold / reconstruction 之前還存在更上游的 provider valid-time alignment 問題。

`.10.9.4` TWS106 CASE：

- event 0°：2026-09-14 10:00:21 UTC；
- event −6°：10:26:48 UTC；
- native GFS request：06Z f003；
- native valid time：09:00 UTC；
- 相對事件 stale 約 60–87 min。

`.10.9.5` 修正後，同一事件區間解析為 06Z f004（10:00 UTC）。

## `.10.9.5` 範圍

只修 provider temporal alignment + provenance/integrity：

- f000–f120 hourly；
- f123–f384 3-hourly；
- pgrb2 / pgrb2b 同 resolver；
- audit 顯示 target/valid/offset/cadence；
- Integrity gate 防止未來靜默退回 blanket 3-hour rounding。

不調 condensate threshold，不改 cloud-column assembly，不動 Frozen PhysicsCore。

## Regression status

- working-tree: **715/715 PASS**
- warning: 1 existing pandas `FutureWarning`
- Field status: **REGRESSION PASS / FIELD RETEST CANDIDATE**

## 下一步

以 `.10.9.5` 正式重跑 TWS106（優先）與 TWS111（交叉驗證），確認 native request 已改為事件對齊的 hourly forecast hour，再判斷 0–100 km native condensate 是否仍為零。只有在 hourly-aligned CASE 仍漏失低雲時，才繼續追 CLWMR/ICMR raw values、pressure-level vertical support、threshold 與 cloud-column assembly。

## Release gate

- clean source files: **805**
- cache/pyc contamination: **0**
- fresh-extract regression: **715/715 PASS**

- FULL-CLEAN ZIP entries: **819**
