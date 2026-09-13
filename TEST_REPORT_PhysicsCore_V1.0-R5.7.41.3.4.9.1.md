# Test Report — V1.0-R5.7.41.3.4.9.1

- Targeted precipitation/context tests：9/9 PASS
- Full regression：643/643 PASS
- Warning：1 個既有 pandas FutureWarning
- Exact-equivalence：legacy rebuild vs prepared native hydrometeor context 使用 `pd.testing.assert_frame_equal(..., check_exact=True)` PASS。
- Science contract：無權重、閾值、六波段、ray sampling、Missing semantics 變更。
