# PhysicsCore V1.0-R4.3 Implementation Status

## Completed in R4.3
- Shared Adaptive Horizontal Sampling remains active: 0–40 km / 5 km; 40–100 km / 10 km; 100 km+ / 20 km.
- Native-condensate multi-column horizontal support remains the only path for resolved upstream cloud-width inference.
- G0 Canvas-specific Sun→CloudBase ray can produce resolved native-condensate slant path length and slant cloud optical depth.
- Full four-component optical path now closes when gas, aerosol, cloud and precipitation evidence are all available.
- Six-band CloudBaseIllumination can be marked confirmed only after full spectral path completion.
- Added CASE diagnostics for native-condensate support coverage.
- Ray/cloud audit performance improved via direction/distance indexing and ray-altitude caching.

## Still fail-closed / pending
- If native condensate is absent, cloud optical evidence remains GEOMETRY_ONLY / Missing.
- 550 nm gas remains Missing until verified six-band H2O/O2/O3 spectroscopy LUT is available.
- Precipitation optical depth remains Missing unless real path-resolved 3-D hydrometeor optical evidence exists.
- R1/R2 refracted slant RT is not yet connected; current resolved slant integration is G0 geometry.
- Tier-2 refined / multiple-scattering Canvas RT and Stage-4 human-visible spectral color remain future checkpoints.
