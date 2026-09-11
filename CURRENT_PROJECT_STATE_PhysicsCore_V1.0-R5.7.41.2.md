# Taiwan Firecloud PhysicsCore — Current Project State
## V1.0-R5.7.41.2

### 基線
- 前一正式版：V1.0-R5.7.41.1 COT Diagnostic Reconciliation
- 本版：V1.0-R5.7.41.2 Production COT Semantic Migration Contract / Shadow Mode

### 已知物理語義
R5.7.41.1 已證明 legacy COT 與 overlap COT 的約 1.81 倍差異可 100% 由 CF scaling、legacy half-cell edge support、pgrb2b vertical resolution 解釋。

R5.7.41.2 不直接替換 Production COT，而是正式區分：
- `LEGACY_CF_SCALED_GRID_CELL_MEAN`
- `IN_CLOUD_EXACT_ENVELOPE_ASSUMED_REFF`

Cloud Fraction / Canvas Coverage 與 COT 分離。

### Shadow eligibility
Candidate 必須通過 target envelope、vertical native evidence、direct conflict、condensate completeness、no-CF/no-RH、r_eff provenance、vertical integration contract 等 gates。

2026-09-11 R5.7.41 Field CASE 離線 replay：
- 767 targets
- 108 `ELIGIBLE_SHADOW_CANDIDATE`
- 659 `INELIGIBLE_SHADOW_CANDIDATE`
- 0 Production switch
- 0 COT promotion
- 0 Formation promotion

### 凍結
- Production COT 尚未切換
- candidate COT 使用 assumed `r_eff`，只能稱 `IN_CLOUD_COT_ESTIMATE_ASSUMED_REFF`
- Missing != Zero != Clear
- CF/RH 不得生成 COT/condensate
- Formation / Viewing / Twilight Glow 分離

### 下一步
1. 累積多 CASE Shadow Mode evidence。
2. 評估 Production semantic switch contract，但不得直接切換。
3. Native GFS 127-level provider 另立版本研究，不與 semantic switch 混版。

### Release Gate
待 working-tree full regression、FULL-CLEAN、fresh-extract full regression 完成後關閉。
