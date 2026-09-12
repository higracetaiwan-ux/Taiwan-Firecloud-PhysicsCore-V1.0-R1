# Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.7.1

## Deployment Import Compatibility Hotfix

本版為 R5.7.41.3.4.7 的部署啟動修正版，不修改任何凍結科學規則、權重、閘門、六波段、Missing semantics、Formation / Viewing / Twilight Glow / Photography Decision。

### 問題

Streamlit Cloud 啟動時發生：

`ImportError` / `ModuleNotFoundError` at `from firecloud.case_archive_stream import write_csv_member_stream`

交付的 R5.7.41.3.4.7 FULL-CLEAN archive 內，`firecloud/case_archive_stream.py` 與 `write_csv_member_stream()` 本身存在且可正常 import；因此錯誤符合部署端出現 mixed worktree / 未同步新 helper 檔案 / stale helper 的情況：`app.py` 已更新，但 engineering-only CASE archive helper 沒有同版本同步。

### 修正

- `app.py` 對 `write_csv_member_stream` 改為 compatibility-guarded import。
- 正常情況仍優先使用 `firecloud.case_archive_stream.write_csv_member_stream`。
- 只有 `ImportError` / `ModuleNotFoundError` 時才啟用 app-local bounded streaming fallback。
- fallback 保留與正式 helper 相同的：
  - UTF-8 CSV payload；
  - bounded coalescing buffer；
  - SHA256；
  - byte count；
  - row count；
  - Missing / DataFrame `to_csv` semantics。
- 不 catch 其他任意 Exception，避免掩蓋真正程式錯誤。

### 驗證

- Deployment import compatibility focused tests：4/4 PASS。
- R5.7.41.3.4.6 / .3.4.7 compatibility targeted suite：PASS。
- Working-tree full regression：635/635 PASS（僅既有 pandas FutureWarning）。
- 模擬 helper import failure 後，fallback 實際寫出 CSV，payload / SHA256 / byte count exact-equivalent。

### Field gate

R5.7.41.3.4.7.1 仍沿用 R5.7.41.3.4.7 的 Field-Test Candidate 狀態。下一個 Field run 仍使用 2026-09-12 Sunset / TWS106 高美濕地 warm CASE，以取得 Viewing / Photography 九段 component-level profiler，確認真正 runtime hotspot。
