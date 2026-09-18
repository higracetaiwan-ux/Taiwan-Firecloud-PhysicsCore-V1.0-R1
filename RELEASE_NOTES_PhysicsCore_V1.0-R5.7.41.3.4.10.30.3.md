# Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.30.3 Release Notes

## Step 3Q.3 — Fu96 Historical Coalbedo Averaging-Equation Qualification

本版延續 `R5.7.41.2_SHADOW_COT_AB_FROZEN`，不改 Formation / Viewing / Twilight Glow、六波段、Canvas、Dynamic Corridor/REZ、Earth Shadow、Production/Shadow COT、Missing≠Clear≠Zero 等 Science baseline。

### 新增資格化內容
- 固定 Fu-lineage broadband coalbedo 的 solar-weighted linear averaging equation。
- 固定 solar-weighted logarithmic averaging equation。
- 固定 mixed equation family：`alpha_eff = h*alpha_linear + (1-h)*alpha_log`。
- 固定 `h` 是 empirical flux-calibration parameter：弱吸收時接近 1，吸收增強時降低；不能只由 absorption strength 直接推導唯一值。
- 明確記錄 RRTM/RRTMG band 24/25 對應的 historical `h` 或 equivalent generator 尚未 recovery。

### Fail-close
- `EXACT_FU96_BAND_WEIGHTING_AVAILABLE = False`
- band 24 / 25 exact reproduction = False
- independent SSA / g validation = False
- `TAU_ICE_PRODUCTION_ALLOWED = False`
- `PRODUCTION_ICE_OPTICS_READY = False`
- physics promotion = False

### Regression
- 941/941 PASS
- 1 個既有 pandas FutureWarning，非 failure。
