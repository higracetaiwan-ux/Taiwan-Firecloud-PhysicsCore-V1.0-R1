# Implementation Status — PhysicsCore V1.0-R5.0

Status: implemented / provider-neutral foundation.

Implemented:
- secondary forecast-native Target Canvas optical evidence schema;
- strict validation and provenance;
- Canvas matching with vertical-overlap checks;
- no sampling-distance-as-cloud-width semantics;
- no CF/RH/geometry-to-COT conversion;
- no primary/secondary averaging;
- explicit multi-source disagreement states;
- CASE export of validated secondary evidence.

Next provider task:
connect an actual forecast-model native cloud microphysics/optics feed (for example ECMWF IFS model-level CLWC/CIWC with vertically resolved geometry) into `snapshot["secondary_target_optics"]`. Observation/satellite sources remain prohibited for forecast mode.
