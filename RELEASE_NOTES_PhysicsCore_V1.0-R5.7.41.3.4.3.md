# Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.3

## DWD Secondary Runtime Cache Hardening

本版延續 R5.7.41.3.4.2，針對近期 Historical Shadow CASE 反覆出現的 DWD ICON secondary provider 重複 I/O 進行純工程修正。

### CASE evidence

2026-08-27 TWS175 與 2026-09-04 TWS021 Historical CASE 中，DWD audit 均出現：

- 54 model levels × QC/QI = 108 個 condensate fields / angle；
- 13 個太陽角度；
- 相同 run/lead 的歷史 DWD OpenData objects 已不存在；
- 總計 1404 筆 `HTTP_404`。

### 修正

1. 新增 process-local native decoded-field cache：相同 run/lead/route geometry 的 QC/QI/T/P 只 decode 一次。
2. Surface pressure/elevation anchor 不納入 native-field cache；各角度 vertical geometry 仍各自重算。
3. 若第一次完整 QC/QI probe 的所有 field 全部為 `HTTP_404`，寫入 process-local run/lead negative availability cache；後續 12 個角度直接 fail-closed，不重送 404 flood。
4. Mixed failure / partial provider response 不會寫 negative cache。
5. 修正 DWD API efficiency audit：HTTP request failure 現在也列入 network request count，並記錄 decoded-field / negative-cache hits。

### 科學契約

不改：

- `R5.7.41.2_SHADOW_COT_AB_FROZEN`；
- Production/Shadow COT；
- Shadow eligibility；
- Earth Shadow / DirectSolarFraction；
- Formation / Viewing / Glow；
- Missing ≠ Clear ≠ Zero。

### 預期效益

Historical all-404 pattern：

- 舊：108 × 13 = **1404** HTTP 404 attempts；
- 新：第一次完整 probe 最多 **108** 次，後續角度 process-local negative cache hit；
- 理論 network-attempt reduction：**92.3%**（13× → 1×）。

Live / available DWD case：native decoded fields 可跨候選角度重用，但 time-specific vertical geometry 不重用。

## Verification

- Working-tree regression: **612/612 PASS**
- Trial fresh-extract regression: **612/612 PASS**
- Final candidate fresh-extract regression: **612/612 PASS**
- Existing pandas FutureWarning: 1 (non-failure)

Exact final archive fresh-extract regression: **612/612 PASS**. Release Gate CLOSED.
