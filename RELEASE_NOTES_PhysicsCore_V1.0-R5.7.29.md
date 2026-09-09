# Taiwan Firecloud PhysicsCore V1.0-R5.7.29 Release Notes

## 本版完成

- 完成 Cloud→Observer Viewing 的 550–750 nm 六波段 component-separated RT。
- Full transmission 現在要求 Gas、CAMS aerosol、cloud 與 forecast-native
  precipitation 四項全部 resolved；partial component tau 不再被誤升格。
- target COT 與 precipitation 改以 time + angle + target identity 綁定，修正跨角度
  重複 layer/canvas ID 可能串錯證據的風險。
- Viewing route snapshot 移至 GFS native hydrometeor merge 後建立，讓
  RWMR/SNMR/GRLE 能進入 Cloud→Observer precipitation path。
- local eligible target 會輸出 explicit unresolved row，確保 target coverage 完整。
- Viewing summary 與 Photography Decision 保存六波段 mean transmission、Full /
  Partial / Unresolved counts 與 completeness。
- 新增五項 R5.7.29 Analysis Integrity checks，並強制 CASE 保存三份 Viewing RT
  evidence tables。

## Frozen contracts

Formation=`Sun→CloudBase`、Viewing=`Cloud→Observer`、Glow independent；無單一
Physics Score。13 angles、六波段、route invariance/resolution、Forecast only
Photography Decision、Missing≠Clear≠Zero≠N/A 全部維持。沒有新增固定 AOD、
Angstrom、O3、synthetic COT、攝影權重或校準門檻。

## 驗證

- R5.7.29 Viewing/Integrity 專項：32 passed / 0 failed。
- Working tree 完整 regression：473 passed / 0 failed。
- R5.7.28 實拍 CASE 離線重播：484/484 eligible targets 保留；451 Partial、
  33 local Geometry-Unresolved；Photography 13/13 rows。
- 舊 CASE 對比：Formation state、Photography opportunity 與 Photography outcome
  各 0 筆變更。
- 舊 CASE 未封存 merged Viewing route hydrometeor snapshot，因此不能事後合成
  precipitation Full RT；必須以 R5.7.29 部署 CASE 完成 field validation。
- FULL-CLEAN 解壓 regression：473 passed / 0 failed。

