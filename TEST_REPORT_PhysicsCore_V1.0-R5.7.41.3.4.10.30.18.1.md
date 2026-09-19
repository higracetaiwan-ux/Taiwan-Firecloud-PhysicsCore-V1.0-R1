# TEST REPORT — PhysicsCore R5.7.41.3.4.10.30.18.1

- CAMS targeted regression：28/28 PASS
- Step3Q lineage：60/60 PASS
- Full collection：987 tests
- Full regression：987/987 PASS
- Failures：0
- Warning：1 個既有 pandas FutureWarning

新增測試覆蓋：
1. reattach-only 無 journal 時禁止 fresh submit；
2. reattach-only 對 durable request ID 使用同一 request 收割完成結果；
3. serial scheduler 可在同一次 run 對 `TIMEOUT_DEFERRED` 執行 bounded same-request-ID reattach 並恢復為 OK。
