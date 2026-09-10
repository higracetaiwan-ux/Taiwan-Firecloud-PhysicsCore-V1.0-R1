# Taiwan Firecloud PhysicsCore V1.0-R5.7.37 實作狀態

## 已完成

- CAMS ML137 O₃ 原生 request / decode / route handoff。
- Open-Meteo surface T/RH/pressure evidence。
- ML137 pressure / height / H₂O / O₂ / O₃ near-surface anchor 建構。
- Rayleigh observer path bracket closure。
- HITRAN gas-species observer path bracket closure。
- 原 pressure-level-only gap provenance 保留。
- 10 m tolerance frozen Integrity guard。
- Missing-evidence fail-close tests。
- CAMS 5-role serial/stateful scheduler contract 更新。

## 測試

完整 regression：
- Working tree：**533/533 PASS**。
- FULL-CLEAN 解壓後：**533/533 PASS**。
- 封包 hygiene：**506 個檔案成員，0 cache/pyc**。

## 尚未完成

- 真實 R5.7.37 CASE field validation。
- CAMS ML137 provider 在 production CASE 的實際成功率與時間統計。
- 台灣既有 `−6° / 100 km / 3.75 km` 三個 rows 是否由新 native evidence 變為 resolved 的 field confirmation。

## 狀態

- Code：CLOSED
- Regression：CLOSED（working / extracted 均 533/533 PASS）
- FULL-CLEAN：CLOSED
- Field Validation：OPEN
