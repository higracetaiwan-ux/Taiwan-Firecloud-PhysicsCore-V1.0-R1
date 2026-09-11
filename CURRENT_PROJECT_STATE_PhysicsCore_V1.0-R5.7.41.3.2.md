# Taiwan Firecloud PhysicsCore — Current Project State

## V1.0-R5.7.41.3.2

本版為 Direct Conflict Eligibility Handoff Hotfix。

### Field trigger
2026-09-12 sunrise / TWS059 野柳岬 R5.7.41.3.1 CASE 自然觸發 39 個 `CONDENSATE_CLOUD_CF_LOW` conflict rows。R5.7.41.3.1 qualifier 已正確辨識，但 overlap / Shadow migration eligibility 未同步，造成 585/585 eligible 的錯誤 Shadow cohort summary。

### 修正後離線 replay
- targets：585
- eligible：546
- ineligible：39
- ineligible reasons：`DIRECT_EVIDENCE_CONFLICT;VERTICAL_INTEGRATION_CONTRACT_FAILED`
- conflict candidate COT finite count：0
- Production switch / COT promotion / Formation promotion：全部 0
- migration Integrity handoff：PASS

### Science baseline
`R5.7.41.2_SHADOW_COT_AB_FROZEN`

### 不改動
Production COT、Formation、Viewing、Twilight Glow、Photography、六波段、太陽角度、Canvas/blocker/Missing 規則均不改。

### 下一步
完成 R5.7.41.3.2 FULL-CLEAN release gate；正式 cohort 以修正後 eligibility 統計為準。

### Release Gate
Working-tree regression：594/594 PASS；FULL-CLEAN fresh-extract regression：594/594 PASS；1 個既有 pandas FutureWarning，非失敗；Release Gate：CLOSED。
