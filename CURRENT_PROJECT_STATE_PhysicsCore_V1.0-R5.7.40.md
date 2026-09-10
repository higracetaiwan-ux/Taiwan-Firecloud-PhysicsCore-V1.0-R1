# Taiwan Firecloud PhysicsCore — Current Project State
## V1.0-R5.7.40

目前正式開發主線：Canvas Optical Truth。

已完成並保留：R5.7.36 Low-Cloud Role Separation、R5.7.37 Near-Surface Molecular Boundary Closure、R5.7.38 CAMS post-success download telemetry/recovery code、R5.7.39/39.1 GFS pgrb2b intermediate native condensate probe與endpoint hotfix。

R5.7.39.1 真實 CASE：pgrb2b f003/f006 HTTP 200，各 45 route rows；432 Canvas 均有 probe evidence；Canvas 範圍內 125 hPa condensate 0/432 positive，因此不能以 125 hPa 補值解掉原 `CF_CLOUD_CONDENSATE_ZERO`。Formation/COT 與 R5.7.38逐列一致。

R5.7.40：新增主 pgrb2 + pgrb2b native vertical conflict qualification。pgrb2b 僅作 hydrometeor context；不使用其中 cloud fraction 作幾何/COT。輸出 isolated CF spike / intermediate support / adjacent primary support / zero intermediate / incomplete context。不得 promotion COT/Formation。

回歸：Focused 20/20；Full 562/562。Field validation OPEN。

下一步：用 R5.7.40 真實 CASE確認 150↔100/125/175/200 hPa vertical context；證據完成後才決定 Canvas Optical Truth Phase 2 是否有資格建立更精確 native target optical evidence。

## Release Gate
- Working regression：562/562 PASS
- FULL-CLEAN：CLOSED
- Extracted regression：562/562 PASS
- cache / pyc：0
- Field validation：OPEN
