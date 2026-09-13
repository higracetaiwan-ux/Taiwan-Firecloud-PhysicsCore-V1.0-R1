# Taiwan Firecloud PhysicsCore — Current Project State

## Current release

**V1.0-R5.7.41.3.4.10.4 — Viewing / Glow Gas Spectroscopy State Memo**

Science baseline remains frozen at **R5.7.41.2_SHADOW_COT_AB_FROZEN**.

## 最新 Field 結果

`.3.4.10.3｜2026-09-13 sunset｜TWS134`：

- Analysis Integrity 72/72 PASS
- CASE Integrity 32/32 PASS
- Glow Observer Precipitation 14.309 → 5.463 s（−61.8%）
- Glow total 42.331 → 25.573 s（−39.6%）
- 67/67 `v1_*.csv` 與 `.10.2` byte-identical
- `.3.4.10.3 = FIELD PASS`

## `.3.4.10.4` 工作

下一個 Glow 第一大戶為 Observer Spectral Extinction 8.533 s。

`.10.4` 對 repeated Gas RT spectroscopy lookup 做 exact memo：

- 1092 Glow targets / 8736 gas segments
- exact T/P states：264
- legacy `_sigma_fast()` 約 157k calls
- cache key 含 LUT content signature + gas + wavelength + exact T/P
- 不改 `gas_rt.py` 或 HITRAN/LUT physics

Actual TWS134 gas helper A/B：1092/1092 exact，1.601 → 0.509 s。

Release gate：working-tree 668/668 PASS；FULL-CLEAN fresh-extract 668/668 PASS。

## Runtime roadmap

1. `.10.4` Field 驗證 Observer Spectral Extinction。
2. Field PASS 後重新排名 Glow components。
3. 若 Observer Spectral Extinction 仍居首，再比較 Gas profile interpolation 與 observer-cloud LOS；不預先改 physics。
4. Shadow COT 仍維持 diagnostic-only validation cohort；不得 promotion。
5. Genuine Tier-2 directional scattering 仍需外部 libRadtran/MYSTIC。
