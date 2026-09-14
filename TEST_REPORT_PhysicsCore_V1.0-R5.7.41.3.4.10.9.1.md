# Test Report — V1.0-R5.7.41.3.4.10.9.1

## 1. Targeted exactness

15/15 PASS。

覆蓋：

- `.10.9` cache handoff exactness
- pre-seeded Viewing cache 可直接服務 Glow
- missing LUT signature fallback
- `.10.9.1` handoff-hit telemetry
- intra-Glow hit vs first-miss telemetry
- uncached fallback telemetry
- `.10.8` molecular handoff adjacent behavior
- `.10.4` gas sigma memo adjacent behavior

Telemetry 測試同時確認：新增計數器不改 gas path numerical output。

## 2. Adjacent chain

`.10.1`～`.10.9.1` Viewing / Glow / Gas runtime chain：**48/48 PASS**。

## 3. Full working-tree regression

**695/695 PASS**。

Warning：1 existing pandas `FutureWarning`，不是新 failure。

## 4. Source audit vs `.10.9`

`firecloud/*.py` baseline 共 61 個：

- 58 byte-identical
- changed：
  - `firecloud/twilight_glow.py`：diagnostic counters only
  - `firecloud/model.py`：diagnostic export only
  - `firecloud/__init__.py`：version only

另外 `app.py` 只更新版本顯示字串。

`gas_rt.py` 未修改；Formation / COT / Shadow / Photography modules 未修改。

## 5. Field evidence inherited from `.10.9`

TWS095 2026-09-14 sunset：

- Volume Assembly = `2.531329 s`
- `.10.8` baseline = `4.542999 s`
- Glow total = `8.606167 s`
- Analysis Integrity = 70 PASS + 1 N/A
- CASE Integrity = 32/32 PASS

`.10.9.1` 尚需新的 Field CASE 來確認新 telemetry 確實輸出並顯示 inherited cache handoff hits。
