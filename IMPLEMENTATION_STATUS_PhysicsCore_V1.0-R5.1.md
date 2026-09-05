# PhysicsCore V1.0-R5.1 Implementation Status

Implemented:
- R5.0 multi-source Target Canvas arbitration.
- ECMWF IFS hybrid model-level GRIB decoding and native CLWC/CIWC optical bridge.
- Configured local/mounted IFS forecast source with explicit fail-closed audit.
- Formation causal gate diagnostics separate from Viewing.

Still unresolved by design:
- Automatic ECMWF network acquisition is entitlement/catalogue dependent and is not guessed. An entitled IFS GRIB must be mounted/configured unless a deployment-specific acquisition adapter is added.
- Primary-vs-secondary direct conflicts remain unresolved and are never averaged away.
- Precipitation path optics still require true 3-D hydrometeor optical evidence.
