# R5.7.23.4 Integrity Audit Robustness 規格

## 目的

保證 provider audit 的 mixed-type 欄位（str / int / float / NaN / None）永遠不能讓 Analysis Integrity 本身崩潰。

## Type-safe row serialization

所有需要 row-wise 搜尋 role/token 的 audit 欄位必須逐 scalar 正規化：

- NaN / NA → 空字串
- None → 空字串
- 其他 scalar → `str(value)`

禁止使用可能重新暴露非字串 scalar 的 `DataFrame.agg(" ".join, axis=1)` 作為 integrity 判定核心。

## CAMS role completeness

同一 CAMS role 跨多個 valid times 時，若任一 matching row 出現：

- TIMEOUT
- FAILED
- ERROR
- HTTP 429
- HTTP 4xx / 5xx

則該 role 不得判為完整成功。

這只影響 evidence/completeness，不允許改寫氣象物理值。

## Timeout 可見性

`CAMS_PROVIDER_TIMEOUT_VISIBLE`：

- 0 timeout → PASS
- >=1 timeout → WARN

WARN 不等於分析程式失敗；它代表 provider evidence 不完整，後續物理輸出應依既有 Missing / Partial contract 處理。
