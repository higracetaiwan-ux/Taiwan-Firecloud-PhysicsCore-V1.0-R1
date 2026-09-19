# Taiwan Firecloud PhysicsCore V1.0 — Release Notes

## 1.0.0-R5.7.41.3.4.10.30.18

**名稱：Step 3Q.18 — Fu96 Primary Spectral Boundary + Band-24 Non-Associative Re-Averaging Barrier Qualification**

### 本版新增
- Pin Fu96-lineage 的 primary solar spectral boundary：`0.700 μm`，相鄰原始 bands 為 `0.2–0.7 μm` 與 `0.7–1.41 μm`。
- 確認 RRTMG Band 25 (`0.441501–0.625000 μm`) 完全位於單一 Fu96 primary band。
- 確認 RRTMG Band 24 (`0.625000–0.778210 μm`) 跨越 Fu96 `0.700 μm` primary boundary。
- 新增 Band-24 inverse re-averaging barrier：因 Fu96-lineage co-albedo 保留 extinction-weighted linear/log spectral moments，再依 absorption strength 混合；compact final broad-band table 不保留這些 pre-averaging moments，因此不能由 final tables 唯一反解歷史 Band-24 generator。
- 新增 portable verifier：`tools/verify_fu96_band24_inverse_reaveraging_barrier.py`。

### 不變
- Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`。
- Formation / Viewing / Twilight Glow、六波段、Canvas / Corridor / REZ、Missing≠Clear≠Zero 全部不變。
- `RRTM_SW_PREAVERAGING_GENERATOR_RECOVERED=False`。
- `PREAVERAGING_SPECTRAL_SAMPLES_RECOVERED=False`。
- `RRTMG_BAND24_EXACT_REPRODUCTION_PASS=False`。
- `RRTMG_BAND25_EXACT_REPRODUCTION_PASS=False`。
- `EXACT_FU96_BAND_WEIGHTING_AVAILABLE=False`。
- `TAU_ICE_PRODUCTION_ALLOWED=False`。
- `PRODUCTION_ICE_OPTICS_READY=False`。
- Step 3R 仍 blocked。
