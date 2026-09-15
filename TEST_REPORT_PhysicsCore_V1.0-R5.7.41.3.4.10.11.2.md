# Test Report — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.11.2

## Working tree regression

`python -m pytest -q`

- **766 passed**
- **0 failed**
- **1 warning**
- warning 為既有 pandas `FutureWarning`，非本版新增 science/runtime failure。

## Ice Optics targeted gate

涵蓋：

- Phase-1 shared Ice runtime
- authoritative Yang/Bi source pipeline
- Portable V1.1 decoupling
- Dmax runtime alignment
- bundled certified portable artifact integrity

目前 targeted tests 全數 PASS。

## `.10.11.2` 新增驗證

1. Positive IWP + r_eff but no Dmax → `ICE_MAXIMUM_DIMENSION_MISSING`
2. wavelength-dependent source-derived r_eff 不得改寫 Dmax lookup
3. bundled portable LUT explicit load → 30,618 rows / 5,103 six-band groups
4. bundled portable LUT SHA256 matches Portable V1.1 manifest
5. bundled Portable ZIP SHA256 matches pinned certification:
   `802d82b49cef4e20a4458bc50f063133a58b19fcfcb4e49941cc8ca16f7afd05`

## Science boundary

- `physics_promotion_allowed=false`
- Formation / Viewing / Twilight Glow frozen science unchanged.
- Bundled portable LUT is certification/reproducibility artifact and is not auto-activated into production runtime.

## Fresh extract

FULL-CLEAN candidate fresh-extract：**766 passed / 0 failed / 1 existing pandas FutureWarning**。
候選 ZIP 解壓後重新執行完整 pytest，結果與 working tree 一致。
