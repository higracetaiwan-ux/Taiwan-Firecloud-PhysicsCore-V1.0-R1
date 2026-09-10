# Taiwan Firecloud PhysicsCore V1.0-R5.7.36 發行說明

## 主要修正

- 低雲（雲底 <2 km）不再進入 Formation Canvas target chain。
- 低雲仍保留在 CloudScene，可繼續作上游阻光與 Viewing obstruction。
- >100 km 雲層不再標成 Formation Canvas target。
- 新增 Formation cloud role 與 eligibility provenance。
- 新增 `FORMATION_CANVAS_LOW_CLOUD_ROLE_SEPARATION` Integrity guard。

## 真實 CASE 對照

- 日本 2026-09-10 CASE：舊版 585 個低雲 Canvas → 新規則 0 個有效 Formation Canvas。
- 台灣 2026-09-10 CASE：312 個有效 Canvas → 新規則仍為 312 個，沒有誤刪。

## Regression

正式封包前 working-tree：524/524 PASS。

## Field Validation

新程式實跑 CASE：OPEN。舊 CASE 不修改。
