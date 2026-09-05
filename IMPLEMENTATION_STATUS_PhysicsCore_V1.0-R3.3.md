# PhysicsCore V1.0-R3.3 Implementation Status

## Active
- V1.0 nine-angle Core runtime
- Native CloudScene / CanvasCandidate / DirectSolarFraction G0 foundation
- Canvas-specific ray-cloud intersections
- Six-band OpticalPath contracts
- R3.1 Missing cloud-optics semantics and native vertical support
- CAMS native aerosol + real O3 profile path
- R3.2 six-band gas runtime activation/validation
- R3.3 Canvas-candidate RT filtering (default)
- R3.3 shared GasRTPreparedContext
- R3.3 cached route spectral-AOD handoff

## Still incomplete by design
- Verified complete 550-nm H2O/O2/O3 Runtime LUT is not packaged; 550-nm gas remains Missing until built/imported
- Cloud optical evidence may remain GEOMETRY_ONLY when native condensate/COT is unavailable
- Precipitation 3-D optical depth remains unresolved without hydrometeor optical evidence
- R4 Canvas Optical Response / Formation not yet connected
- Viewing / Glow / Decision remain later stages

## Performance acceptance
R3.3 changes the execution structure to remove the legacy all-voxel target RT from the default V1 path. The live same-event CASE is required to quantify wall-clock improvement because CAMS request time is external and variable.
