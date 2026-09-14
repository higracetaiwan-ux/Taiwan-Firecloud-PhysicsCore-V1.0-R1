# Test Report — PhysicsCore V1.0-R5.7.41.3.4.10.10.1

## Targeted

Ice Phase 1 + Portable decoupling tests：PASS。

Portable-specific coverage：

- runtime dependency contract = NONE
- package required members
- manifest SHA256/byte-size verification
- empty/un-calibrated LUT build refusal
- ZIP contains no Python runtime files
- Python generated vectors ↔ dependency-free Node evaluator parity
- standalone TypeScript evaluator strict compile
- Integrity `ICE_OPTICS_PORTABLE_WINDY_RUNTIME_DECOUPLING`

## Full regression

`748 passed, 1 warning`。

Final FULL-CLEAN fresh-extract：`748 passed, 1 warning`。

Warning 為既有 pandas FutureWarning，不是本版 regression。

## Frozen science audit

16/16 frozen science files byte-identical vs `.10.10`。

## Release gate

REGRESSION PASS。Field retest / calibrated LUT science certification 尚未完成，因此不是 Ice LUT science FIELD PASS。
