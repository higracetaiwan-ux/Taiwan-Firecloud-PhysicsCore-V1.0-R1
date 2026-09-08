# R5.7.27.1 Photography Integrity Handoff 規格

## 目的

R5.7.27 已完成 Formation-first Photography Decision，但 Analysis Integrity
必須接收到同一份已建立、將回傳並匯出的 `v1_photography_decision`，才能正確
檢查角度覆蓋與 Formation NO-GO dominance。

## 凍結的 handoff 契約

`model.py` 在呼叫 `build_analysis_integrity_audit()` 前，
`_pre_integrity_result` 必須包含：

```text
v1_photography_decision → v1_photography_decision
```

不得在 Integrity 內重新計算 Photography Decision，也不得使用 Viewing 或
legacy score 重建另一份結果。Integrity 只驗證主 pipeline 已產生的正式表。

## CASE 封存契約

`v1_photography_decision.csv` 是 R5.7.27+ CASE 的 required member。缺少時：

- `ARCHIVE_MEMBER::v1_photography_decision.csv = FAIL`
- `CASE_ARCHIVE_INTEGRITY_OVERALL = FAIL`

CASE 仍可供 forensic 下載，但不得宣稱封存完整。

## 不變事項

- Formation = `Sun→CloudBase`
- Viewing = `Cloud→Observer`
- Glow 為獨立第三分支
- 13 個核心角度不變
- 六波段不變
- Route Invariance 不變
- 物理權重與門檻不變
- Missing、Clear、Zero、Not Applicable 仍彼此不同

