# Test Report — V1.0-R5.7.41.3.4.10.1

## Working tree
- Targeted Viewing/Glow regression：19/19 PASS
- Full regression：654/654 PASS
- Warning：1 個既有 pandas FutureWarning，非 failure。

## Actual CASE A/B
TWS106 `.3.4.10` evidence reconstructed into identical target inputs。
- Glow：1092 targets；legacy/optimized output `check_exact=True`。
- Main Viewing：585 targets；legacy/optimized output `check_exact=True`。
- Glow observer spectral wall time（standalone same process style）：6.116 → 3.440 s。
- Main Viewing spectral wall time：3.105 → 1.843 s。
- Runtime-context preparation 約增加 0.7–0.8 s，一次性成本。

上述為 local/offline benchmark，不等同 Field Streamlit speedup。

## Fresh-extract gate
- FULL-CLEAN fresh-extract regression：654/654 PASS。
- 1 個既有 pandas FutureWarning，非 failure。
- Release gate：CLOSED。
