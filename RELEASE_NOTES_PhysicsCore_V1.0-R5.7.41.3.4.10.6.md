# Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.6 Release Notes

## 名稱

**Viewing / Glow Cloud Numeric Route Context**

## 前一版 Field verdict

`.3.4.10.5` TWS134：

- 72/72 Analysis Integrity PASS
- 32/32 CASE Integrity PASS
- 67/67 `v1_*.csv` byte-for-byte identical vs `.10.4`
- Observer Spectral Extinction 6.642 → 7.085 s
- `.10.5 = science exactness PASS / runtime NOT FIELD PASS`

## 本版變更

- 版本提升為 `1.0.0-R5.7.41.3.4.10.6`。
- 新增 exact-order cloud numeric route context，避免每個 Viewing/Glow target 重新對相同 cloud route 做 DataFrame copy/filter/iterrows。
- projected support 仍由 frozen Viewing helper 計算並沿用同一 cache。
- 保持 cloud row 原順序、25-point LOS、COT/CF、occupancy expectation、conflict/Missing diagnostics 與 τ 累加順序。
- exact route 沒有 prepared cloud context 時保留 legacy helper fallback。

## Actual TWS134 A/B

- Main Viewing 585 targets：legacy / `.10.6` 完整 DataFrame `check_dtype=True, check_exact=True`。
- Glow 1092 targets：legacy / `.10.6` 完整 DataFrame `check_dtype=True, check_exact=True`。
- Main CSV SHA256：`450f38d12db5d4eb2d27f0ce1c7f7495ac5105b644afbf40e3e09a182a23cdd7`
- Glow CSV SHA256：`1eecc0585f520e4d3f5162fbf121600afbbf7633bfd57ca610242b22f8005870`

本版目前為 **FIELD TEST CANDIDATE**；不得在新的 TWS134 CASE 回來前宣稱 Field speedup。
