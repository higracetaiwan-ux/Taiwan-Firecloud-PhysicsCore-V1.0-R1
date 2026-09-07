# Implementation Status — PhysicsCore V1.0-R5.7.12

Shared Geometry Core V1.4 is active. Earth/ray geometry, voxel intersection topology/materialization, segment sampling, slant accumulation, and vertical-cell indexing now have shared authoritative implementations. Legacy interfaces remain compatibility façades.

Still intentionally deferred: Taiwan Geometry Atlas, persistent observer geometry library, cross-provider forced vertical-grid unification, and wavelength-dependent refracted-ray atlas. Different provider lattices are never forced to share an index plan unless geometry coordinates are compatible.


R5.7.12 also corrects target-applicability semantics: complete-zero native condensate is `AVAILABLE_PHYSICALLY_ZERO`; target-dependent spectral RT is `NOT_APPLICABLE` when no Canvas target exists. These N/A layers do not lower operational input completeness. Missing input, physical zero, and no-target applicability remain separate states.
