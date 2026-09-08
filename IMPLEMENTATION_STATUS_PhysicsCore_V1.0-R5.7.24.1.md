# Taiwan Firecloud PhysicsCore V1.0-R5.7.24.1 實作狀態

## 已完成

- R5.7.24 Runtime Reliability / Completion Guarantee
- R5.7.24 Memory Containment
- per-angle heavy evidence `/tmp` spool
- route snapshot spool / Viewing snapshot containment
- provider cache post-angle release
- `MALLOC_ARENA_MAX=2`
- `malloc_trim` / GC boundary
- non-blocking Streamlit worker monitoring
- recovery journal redundancy
- CAMS role live telemetry
- CASE integrity type safety
- **CAMS availability guard 12.25 h**
- **HTTP 400 invalid-combination 非空間型錯誤 fail-fast**
- adaptive spatial subdivision 僅保留給可能由空間切割改善的失敗類型

## 仍屬外部條件

- CAMS ADS queue / publication latency 仍可能波動
- DWD / GFS / Open-Meteo 網路可用性仍由外部服務決定
- genuine libRadtran / MYSTIC production LUT 尚未安裝

## Production LUT 狀態

`CALIBRATED DIRECTIONAL LUT NOT INSTALLED`

不得以 synthetic LUT 代替。

## 驗收原則

本版優先驗證：

1. 分析能否正常完成
2. CAMS cycle 是否選到可用的已發布 cycle
3. HTTP 400 是否快速終止而不進行無效 spatial recursion
4. Missing evidence 是否正確留在完整性稽核
5. RSS 是否維持 R5.7.24 的記憶體改善
6. 核心 Physics/Formation/Viewing 結果不得因 runtime 修正漂移
