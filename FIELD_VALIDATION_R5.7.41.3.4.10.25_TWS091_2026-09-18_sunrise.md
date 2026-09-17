# FIELD Validation Memo — R5.7.41.3.4.10.25

## Case
- Site：TWS091 日月潭朝霧碼頭
- Event：2026-09-18 sunrise
- Program version：`1.0.0-R5.7.41.3.4.10.25`
- Analysis mode：WARM_PRODUCTION

## Archive / integrity
- CASE archive entries：186。
- `case_archive_manifest.csv` WRITTEN members checked：184。
- Missing members：0。
- SHA256 mismatches：0。
- `CASE_ARCHIVE_INTEGRITY_OVERALL`：PASS，0 hard failures。
- Analysis integrity upstream hard failures：0。

## Step 3L
- Evidence：12 rows；與 release byte-exact。
- Gate：1 row；與 release byte-exact。
- Contract：完整存在，fail-close integrity PASS，但與 release **not byte-exact**。
- Contract semantic differences 限於兩個 diagnostic sample 尾數：
  - `max_bulk_ssa_spread`
  - `max_grid_convergence_relative_error`

## Positive-IWP runtime evidence
- `native_iwp_kg_m2 > 0` runtime rows：10。
- max native IWP：約 `6.034017421272911e-05 kg/m²`。
- positive-IWP rows：`ice_habit=UNKNOWN`、`surface_roughness=UNKNOWN`。
- `tau_synthesis_allowed=false`。
- `formation_promotion_allowed=false`。

## Result
**FIELD BLOCKED — deterministic contract serialization reproducibility。**

這不是 Frozen Science 或 runtime gate failure；它是證據封存的跨平台 reproducibility blocker。因此 `.10.25` 不列 FIELD PASS，正式 FIELD baseline 仍為 `.10.24.1`。修正版本為 `.10.25.1`，需重新產出 CASE 驗證後再決定 FIELD 狀態。
