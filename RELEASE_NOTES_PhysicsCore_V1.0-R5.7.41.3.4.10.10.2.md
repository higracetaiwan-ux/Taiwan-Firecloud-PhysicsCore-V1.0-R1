# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.10.2

## UI Information Architecture Cleanup

這是一個 **UI-only / documentation-structure release**。Frozen Science baseline 維持 `R5.7.41.2_SHADOW_COT_AB_FROZEN`。

### 改善

- 頁首只顯示現行版本、Science Baseline 與里程碑，不再直接展開全部歷史版本文字。
- 「模型輸出層」重整為 Formation / Viewing / Twilight Glow 三軌。
- 新增 Cloud Optical Physics、Ice Optics、Frozen Science、最近版本、歷史科學、Runtime/Provider 歷史折疊區。
- 左側資料來源改成結構化來源清單並明示 `Missing ≠ Clear ≠ Zero`。
- 背景分析將 Job/PID/attempt 移入 Runtime 詳細資訊。
- `.10.10.1` PhysicsCore↔WINDY runtime decoupling contract 完整保留。

### 不變

- 不改 Formation / Viewing / Twilight Glow。
- 不改六波段 550/575/600/650/700/750 nm。
- 不改 Canvas、Dynamic Corridor/REZ、Earth Shadow、Production/Shadow COT。
- 不改 CLWMR/ICMR thresholds 或 Missing semantics。
- 不改 Ice Optics science contract / portable evaluator。

### 驗證

- targeted UI tests 4/4 PASS
- full working-tree regression 752/752 PASS
- final FULL-CLEAN fresh-extract regression 752/752 PASS
- frozen science files 16/16 byte-identical vs `.10.10.1`
