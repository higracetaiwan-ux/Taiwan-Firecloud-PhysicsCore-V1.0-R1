# Implementation Status — V1.0-R5.7.41.3.4.10.4

## 狀態

**IMPLEMENTED / REGRESSION PASS / FIELD TEST PENDING**

## 已完成

- `.3.4.10.3` TWS134 Field PASS。
- 67/67 `v1_*.csv` `.10.2 ↔ .10.3` byte-identical。
- spectroscopy LUT content signature。
- exact T/P state sigma memo。
- main Viewing 與 Twilight Glow 共用同一 runtime context / cache。
- legacy fallback：若沒有 memo/signature，仍走原 `_sigma_fast()` 路徑。
- targeted exact-equivalence tests。
- working-tree full regression：668/668 PASS。
- FULL-CLEAN fresh-extract regression：668/668 PASS。
- `.10.3 → .10.4` `firecloud/*.py`：僅 `__init__.py` 與 `viewing_spectral.py` 變更；其餘 78/80 byte-identical。

## Field gate

新 CASE 主要看：

`TWILIGHT_GLOW_COMPONENT_OBSERVER_SPECTRAL_EXTINCTION`

基準：`.3.4.10.3 TWS134 = 8.533 s`。

只有 Field CASE 明顯下降，才將 `.3.4.10.4` 標成 FIELD PASS。
