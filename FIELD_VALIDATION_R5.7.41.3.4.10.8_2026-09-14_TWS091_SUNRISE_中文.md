# R5.7.41.3.4.10.8 Field Validation — 2026-09-14 TWS091 Sunrise

## 結論

**FIELD PASS**。

`.10.8 Viewing→Glow Molecular Context Handoff` 的主要 Field gate 明確成立。

## Integrity

- Analysis Integrity：70 PASS + 1 NOT_APPLICABLE（共 71 項）
- CASE Integrity：32/32 PASS
- 唯一 NOT_APPLICABLE：`NEAR_SURFACE_MOLECULAR_BOUNDARY_BRIDGE_PROVENANCE`，本次 `bridged_rows=0`，屬正常狀態。

## Glow runtime A/B

`.10.7 → .10.8`（TWS091 / 2026-09-14 sunrise）：

- Lookup Context Prep：6.647128 → **0.256652 s**（−96.1%，約 25.9×）
- Volume Assembly：7.226424 → **4.542999 s**
- Observer Spectral Extinction：3.087648 → **1.764785 s**
- Observer Precipitation：2.407172 → **1.307537 s**
- Glow total：22.970400 → **10.252142 s**（−55.4%）

因此 `.10.8` 的 shared molecular context 在正式 CASE 中確實命中，且沒有把 preparation 成本搬到 Glow 其他 component。

## Science / provider comparison

67 個 `v1_*.csv` 中 65/67 byte-identical。差異僅：

- `v1_native_condensate_support_diagnostics.csv`
- `v1_secondary_target_optics.csv`

差異追溯到 DWD secondary/native availability evidence 在兩次 run 的 provider state 不同；不是 `.10.8` molecular handoff 對 z/T/P、Rayleigh、HITRAN 或 Glow physics 的改寫。

## 下一個瓶頸

`.10.8` 後新的 Glow 第一大戶為 **Volume Assembly = 4.542999 s**。下一階段只應處理可 exact-reuse 的 Volume Assembly 重複成本，不再優化已降至 0.256652 s 的 Lookup Context Prep。
