# Taiwan Firecloud PhysicsCore V1.0-R5.7.40 實作狀態

- Code：CLOSED
- Focused regression：20/20 PASS
- Full regression：562/562 PASS
- Science scope：Vertical conflict qualification only；未做 COT promotion
- R5.7.39.1 pgrb2b endpoint hotfix：已由真實 CASE確認 HTTP 200 / READY
- R5.7.40 Field validation：OPEN

下一個 field CASE 要確認 primary conflict Canvas 是否全部產生 qualification rows，並檢查 150 hPa 主衝突層的 100/200 hPa 主鄰層與 125/175 hPa intermediate hydrometeor context。

## Release Gate
- Working regression：562/562 PASS
- FULL-CLEAN：CLOSED
- Extracted regression：562/562 PASS
- cache / pyc：0
- Field validation：OPEN
