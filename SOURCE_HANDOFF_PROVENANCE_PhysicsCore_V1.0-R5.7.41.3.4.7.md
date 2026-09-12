# Source Handoff Provenance — V1.0-R5.7.41.3.4.7

本次新聊天室接手時：

- 正式狀態檔指向 `V1.0-R5.7.41.3.4.6`；
- Library 可取得 `.3.4.6` TWS106 Field CASE 與完整 runtime telemetry；
- Library 未找到 `.3.4.6 FULL-CLEAN` source archive；
- 可取得上一個完整 source archive：`.3.4.5 FULL-CLEAN`。

因此本 candidate 使用 `.3.4.5 FULL-CLEAN` 為 source tree，依 `.3.4.6` 記憶檔與 Field CASE 可驗證的 runtime-only contract 恢復：DWD persistent raw cache、API audit、CASE buffered streaming、aggregation profiler；再新增 `.3.4.7` Viewing/Photography component profiler。

凍結 science modules 以 SHA256 對照確認沒有改動。由於缺少 `.3.4.6` source archive，本 candidate 在代表 Field CASE 完成前不宣稱 `.3.4.6 ↔ .3.4.7` source-level exact diff 已被直接證明；必須以 `.3.4.6` CASE science outputs 與 `.3.4.7` 新 CASE 做 byte/SHA exact-equivalence 驗證後才關閉 Field gate。
