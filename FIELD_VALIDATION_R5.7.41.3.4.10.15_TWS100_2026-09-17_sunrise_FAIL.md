# Taiwan Firecloud PhysicsCore V1.0 — R5.7.41.3.4.10.15 FIELD Validation

## 驗證案例
- 版本：`1.0.0-R5.7.41.3.4.10.15`
- CASE：`2026-09-17 sunrise / TWS100 合歡山北峰`
- Runtime：`WARM_PRODUCTION`
- Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`
- FIELD 結論：**FAIL — CASE EVIDENCE ARCHIVE INTEGRITY**

## 核心分析本身
- Worker：`COMPLETED`
- exit code：`0`
- Analysis Integrity：97 checks；85 PASS、5 WARN、4 ALLOWED_EMPTY、3 NOT_APPLICABLE、0 FAIL
- CASE manifest：154 / 154 `WRITTEN`
- manifest SHA256 重算：154 / 154 相符
- CASE Integrity（舊 presence-only gate）：56 / 56 PASS

上述 CASE Integrity 結果是「假 PASS」：它只證明三個 Step 3B 檔名存在，沒有證明內容有效。

## 發現的 FIELD 缺陷
實際 CASE members：
- `ice_microphysics_gfsv16_scheme_pin_evidence.csv`：**1 byte，0 rows，只含換行**
- `ice_microphysics_gfsv16_scheme_pin_gate.csv`：**1 byte，0 rows，只含換行**
- `ice_microphysics_gfsv16_scheme_pin_contract.json`：**2 bytes，內容 `{}`**

但同一 CASE 的 `analysis_integrity_audit.csv` 卻顯示：
- evidence_rows=8
- gate_rows=1
- contract_present=True
- 三個 Step 3B Analysis Integrity checks 都 PASS

原因：Analysis Integrity 驗的是 model 內 `_pre_integrity_result`；CASE export 寫的是 UI/session `result`。兩條 evidence path 沒有被內容級 gate 綁死。Archive Integrity 又只檢查 member presence，因此空 placeholder 被誤判 PASS。

## Ice runtime 科學 fail-close
Ice runtime：2691 rows
- positive IWP：65
- exact-zero IWP：2626
- Dmax non-null：0
- r_eff non-null：0
- resolved habit：0
- resolved roughness：0
- `tau_synthesis_allowed=true`：0
- `formation_promotion_allowed=true`：0
- positive-IWP 六波段 `tau_ice` non-null：0 / 65
- positive-IWP state：65 / 65 `ICE_OPTICS_LUT_UNAVAILABLE`

在 exact-zero IWP rows 中，有 2392 rows 是完整 native-state zero-condensate：
- 六波段 `tau_ice=0`
- 六波段 transmission=1

另有 234 zero-IWP rows 因 native vertical support incomplete 而保持 `ICE_IWP_INCOMPLETE_NATIVE_VERTICAL_SUPPORT`。

因此沒有 `r_eff→Dmax`、IWP→Dmax、PSD reconstruction、habit/roughness default 或 Ice production promotion。

## 效能
- GFS_PREFETCH_TOTAL：8.985 s
- CAMS_PREFETCH_TOTAL：136.400 s
- Step 3B scheme pinning：0.003 s
- TOTAL_ANALYSIS_CORE：339.654 s
- TOTAL_TO_CASE_ARCHIVE：361.636 s

## 結論
`.10.15` **不得升格 FIELD PASS**。

需要 hotfix：
`R5.7.41.3.4.10.15.1 — Step 3B CASE Evidence Handoff Integrity Hotfix`

修補要求：
1. CASE export 必須由當前 release builder 產生 Step 3B release-static evidence；
2. evidence CSV 至少 8 rows；
3. qualification gate CSV 至少 1 row；
4. contract JSON 不得是空 `{}`；
5. Archive Integrity 必須檢查實際 serialized content，而非只檢查檔名；
6. Frozen Science 不變。
