# Taiwan Firecloud PhysicsCore — Current Project State
## V1.0-R5.7.41.3

### 基線
- Science baseline：V1.0-R5.7.41.2 Production COT Semantic Migration Shadow Mode
- 本版：Shadow Validation Collection Readiness / Shared Scenic Spot Selector

### 收集前準備
R5.7.41.3 將觀測地點與 CASE 收集 identity 標準化。景點資料使用台灣晨昏攝影景點母資料庫 V2.2，共 187 個唯一 GPS 景點；預設高美濕地 `TWS106`。自訂座標仍可使用，明確標示 `MANUAL`。

每個 CASE 保存 site identity、event、GFS cycle / forecast hours、runtime job、Shadow candidate counts、Legacy / Shadow COT cohort statistics 與 Ground Truth template。

### Science Freeze
Shadow collection baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`。
收集期間禁止 Production COT switch、COT promotion、Formation promotion；違反即 CASE collection guard FAIL。

### 不改動
- Production COT
- Formation
- Viewing
- Twilight Glow
- Photography
- 六波段／太陽角度／Canvas／blocker／Missing 規則

### 下一步
1. FULL-CLEAN release gate。
2. 一次 Online CASE 驗證 selector / CASE collection artifacts。
3. 正式累積 12–16 個 sunrise / sunset、不同天氣型態的 Shadow CASE。
4. 做第一輪 Shadow Validation Report，再決定是否具備 Production semantic switch 評估資格。
5. Native 127-level provider 仍為獨立後續工作，不在第一批 cohort 中改變 evidence basis。

### Release Gate
CLOSED：working-tree 589/589 PASS；FULL-CLEAN fresh-extract 589/589 PASS；僅 1 個既有 pandas FutureWarning，非失敗。
