# Taiwan Firecloud PhysicsCore — Current Project State

Current release candidate: **V1.0-R5.7.41.3.4.10.9.6 — GFS Native Near-field Source Attribution + Timeline Valid-Time Provenance**

Internal version: `1.0.0-R5.7.41.3.4.10.9.6`

Science baseline remains frozen at **`R5.7.41.2_SHADOW_COT_AB_FROZEN`**.

## 已完成 Field baseline

- `.10.9 = FIELD PASS`
- `.10.9.3 = FIELD PASS + TWS111 CROSS-SITE PASS`
- `.10.9.4 = FIELD PASS`
- `.10.9.5 hourly valid-time alignment = FIELD PASS`（TWS106 正式 CASE）

## `.10.9.5 TWS106` 正式 CASE 結論

- GFS：06Z f004 = 10:00 UTC
- event target：10:00:21.746 UTC
- offset：−21.746 s
- `GFS_NATIVE_VALID_TIME_ALIGNMENT = PASS`
- Analysis Integrity：62 PASS / 5 WARN / 4 ALLOWED_EMPTY / 2 NOT_APPLICABLE / 0 FAIL
- CASE Integrity：36/36 PASS
- 0–100 km native voxel supported rows：21060
- 其中 CLWMR positive = 0、ICMR positive = 0、native TCDC positive = 0
- 585 native columns 的 vertical completeness 全部 1.0，LWP/IWP proxy 全部 0

因此 hourly alignment 修正後，低雲仍沒有出現在 GFS native pressure-level reconstruction。這不是 Missing，也不是 `1e-7` threshold 已知造成的結果；需要 source-level evidence正式區分。

## `.10.9.6` 範圍

1. 新增 0–100 km decoded GFS pressure-level source attribution。
2. 將 exact zero / positive below threshold / positive above threshold / Missing 分開。
3. Observer Timeline native matching 改用 provider `gfs_valid_time_utc`。
4. Timeline 擴展 T−180→T+60 / 5 min，以覆蓋秋季日落前約 2 小時短生命期積雲演變。
5. 所有新增功能都是 diagnostic-only，不得改 Physics decision。

## 下一步 Field

先重跑 TWS106 `.10.9.6`：
- 檢查 source-level low layer 是否 `EXACT_ZERO`；
- 若 source exact zero，正式歸因為 forecast/source underrepresentation，而不是 reconstruction threshold；
- 若 source 有 positive condensate，才往 vertical interpolation / threshold / cloud-column assembly 追。

再以 TWS111 西向 Local Ground Truth 做 cross-site 重跑。

## Regression status

- working-tree: **718/718 PASS**
- draft fresh-extract: **718/718 PASS**
- final FULL-CLEAN fresh-extract: **718/718 PASS**
- FULL-CLEAN entries: **837**
- cache/pyc contamination: **0**
- warning: 1 existing pandas `FutureWarning`
- status: **REGRESSION PASS / FIELD RETEST CANDIDATE**
