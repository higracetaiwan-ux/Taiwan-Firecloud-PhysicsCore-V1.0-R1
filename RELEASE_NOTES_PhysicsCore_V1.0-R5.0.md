# Taiwan Firecloud PhysicsCore V1.0-R5.0

## Secondary Target Cloud Optical Evidence

R5.0 adds a fail-closed multi-source Target Canvas optical-evidence contract.

- A second source is eligible only when it is explicitly a **forecast-model native optical** source with finite COT, geometry, provider and provenance.
- Satellite observations are not accepted as forecast optical evidence.
- Cloud fraction, RH and cloud geometry still never synthesize COT.
- Primary and secondary COT are never averaged.
- Explicit GFS `CF_CLOUD_CONDENSATE_ZERO` conflict is not erased by a positive secondary source; it becomes `MULTISOURCE_DIRECT_CONFLICT_UNRESOLVED`.
- Primary/secondary exact COT disagreement greater than a factor of 2 revokes exact promotion and remains Unknown.
- When primary optics are simply missing (not directly contradictory), a valid secondary forecast-native COT may be promoted as exact target optics with provenance.

New CASE table: `v1_secondary_target_optics.csv`.

This release provides the provider-neutral secondary forecast optical contract and arbitration layer. It does not fabricate a secondary COT when no forecast-model native optical source is connected.
