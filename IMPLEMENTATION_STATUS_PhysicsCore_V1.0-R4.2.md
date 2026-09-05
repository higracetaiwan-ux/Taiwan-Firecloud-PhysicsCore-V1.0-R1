# PhysicsCore V1.0-R4.2 Implementation Status

Implemented:
- Shared adaptive horizontal sampling contract: 5 km / 10 km / 20 km by operational distance domain.
- Adaptive nodes used by route sampling and Canvas/SolarRay geometry.
- Native-condensate multi-column horizontal cloud support inference with explicit provenance.
- G0 slant ray/cloud prism numerical intersection and slant COT integration.
- Upstream blocker COT aggregation separated from target Canvas COT.
- CASE audit tables for sampling and 3D horizontal support.

Fail-closed / deferred:
- Single-column native condensate without adjacent support remains horizontal-support Unknown.
- R1/R2 refracted slant RT is not yet connected; R4.2 slant integration is G0 geometry.
- Precipitation 3D optical volume remains unresolved unless explicit path tau is provided.
- 550 nm gas remains Missing without verified H2O/O2/O3 LUT coverage.
- Firecloud 3D Shared Module will consume the same sampling/support contracts in its integration stage; R4.2 does not duplicate a second 3D physics engine.
