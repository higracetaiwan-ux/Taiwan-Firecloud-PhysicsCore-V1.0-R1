# TEST REPORT — PhysicsCore R5.7.41.3.4.10.30.18.2

- CAMS targeted regression：72/72 PASS
- Step3Q lineage：63/63 PASS
- Full collection：990 tests
- Full regression：990/990 PASS
- Failures：0
- Warning：1 個既有 pandas FutureWarning

新增核心測試：
1. adaptive scheduler `QUEUE_GRACE_EXCEEDED` 可在同 run 用 same request ID reattach；
2. adaptive scheduler `RUNNING_GRACE_EXCEEDED` 可同樣 reattach；
3. bounded reattach 仍 timeout 時保持 Missing，且不啟動 adaptive subdivision。
