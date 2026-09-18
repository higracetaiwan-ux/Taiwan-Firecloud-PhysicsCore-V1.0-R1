# Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.30.4 Release Notes

## Step 3Q.4 — Fu96/RRTMG Historical h-Domain Constraint Qualification

本版延續 `R5.7.41.2_SHADOW_COT_AB_FROZEN`，不改 Formation / Viewing / Twilight Glow、六波段、Canvas、Dynamic Corridor/REZ、Earth Shadow、Production/Shadow COT、Missing≠Clear≠Zero 等 Science baseline。

### 新增資格化內容
- Chou 1998：ice cloud `h=1` for 0.18–0.70 µm，`h=2/3` for 0.70–1.22 µm。
- Chou 2002：bands 1–8（0.175–0.700 µm）`h=1`；band 9（0.700–1.220 µm）`h=2/3`。
- RRTMG band 25：16000–22650 cm⁻¹ = 0.441501–0.625000 µm，完整位於 Fu-lineage `h=1` domain。
- RRTMG band 24：12850–16000 cm⁻¹ = 0.625000–0.778210 µm，跨越 0.700 µm `h` domain boundary；禁止未經 historical generator 證據直接指定單一 `h`。
- 明確區分「lineage domain constraint」與「archived RRTM/RRTMG exact generator provenance」。

### Fail-close
- band 25 的 `h=1` 目前只屬 lineage-domain constraint；未證明其等同 archived RRTMG table generator。
- band 24 historical mixing realization 尚未 recovery。
- `EXACT_FU96_BAND_WEIGHTING_AVAILABLE = False`
- band 24 / 25 exact reproduction = False
- independent SSA / g validation = False
- `TAU_ICE_PRODUCTION_ALLOWED = False`
- `PRODUCTION_ICE_OPTICS_READY = False`
- physics promotion = False

### Regression
- 942/942 PASS
- 1 個既有 pandas FutureWarning，非 failure。
