# PhysicsCore V1.0-R5.2 Implementation Status

Implemented:
- finite solar disk any/center/full transition-height solver
- 10/20/30/40 km Earth-shadow penumbra matrix
- Canvas-level penumbra/red-illumination diagnostic
- Formation gate enriched with finite-disk transition heights
- CASE export for both new diagnostics

Preserved:
- `F_sun` is the core geometry variable; shadow height remains diagnostic.
- no arbitrary red-irradiance threshold
- no observer/viewing-path mixing into Formation
