# PhysicsCore V1.0-R5.7.24 實作狀態

## 已完成

- [x] Detached analysis worker
- [x] Streamlit non-blocking worker monitor
- [x] live worker reload/reattach，避免 duplicate worker
- [x] master + per-job redundant recovery journal
- [x] attempt-specific request/progress/stdout/stderr/result
- [x] recovery journal error log
- [x] route snapshot local temporary spool
- [x] Viewing route snapshot spool
- [x] cloud/gas/aerosol/spectral per-angle evidence spool
- [x] per-angle compact Physics Data Completeness summary
- [x] compact UI-only `details.snapshot`
- [x] per-angle `gc + malloc_trim` best-effort memory return
- [x] glibc worker allocator containment environment
- [x] post-angle provider in-memory cache release
- [x] R5.7.23.4 CASE-integrity type safety preserved
- [x] R5.7.23.3 CAMS live telemetry preserved
- [x] R5.7.23.2 memory-safe aggregation preserved
- [x] R5.7.22.1 Route Invariance preserved

## 驗收狀態

- Unit / regression：**428 passed / 0 failed**
- 需要部署後以真實 `COLD_ISOLATED_TEST` 再驗證 RSS 曲線是否較 R5.7.23.4 的約 786 → 1,000+ MB 明顯收斂。
- 真實部署驗收標準以「能穩定跑完」為第一優先，不以耗時作本版 fail 條件。

## 尚未完成／不屬於本版

- [ ] CAMS request consolidation / 效能最佳化
- [ ] DWD shared decoded tile cache 效能最佳化
- [ ] 13-angle NumPy/vectorized physics 重構
- [ ] genuine libRadtran/MYSTIC production LUT execution
- [ ] GFS 09Z/10Z temporal interpolation contract

## Production LUT

目前仍為：

`CALIBRATED DIRECTIONAL LUT NOT INSTALLED`
