# Ice Microphysics Wyser Primary Numeric Recovery Qualification — R5.7.41.3.4.10.20.1

- PhysicsCore: `1.0.0-R5.7.41.3.4.10.20.1`
- Science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`
- Qualification: `WYSER_PRIMARY_EQ5_EQ6_NUMERIC_RECOVERED_DIAGNOSTIC_MASS_CLOSURE_PASS_EXTERNAL_EQ6_CORROBORATION_BLOCKED`
- Primary Eq.(5) numeric recovered: `True`
- Primary Eq.(6) numeric recovered: `True`
- Eq.(5)/(6) unit consistency: `True`
- Diagnostic primary Eq.(6) PSD mass closure: `True`
- Diagnostic convergence: `True`
- Independent external Eq.(6) corroboration: `False`
- Scientific mass closure: `False`
- Absolute PSD executable: `False`
- L→Yang/Bi Dmax validated: `False`
- Production Ice Optics ready: `False`

## Diagnostic preflight

- Cases: `18`
- Temperatures (K): `[233.16, 253.16, 273.16]`
- IWC (g m^-3): `[0.001, 0.1, 10.0]`
- Grid points: `[1025, 4097]`; reference `32769`
- Max mass-closure relative error: `3.5527136788005011e-16`
- Max 20 µm continuity relative error: `1.2541086189306697e-15`
- Max normalization convergence relative error: `8.2034382133034755e-07`

> 此 preflight 僅驗證 numeric reconstruction；不建立 operational validity domain，也不能取代 independent external Eq.(6) corroboration。
