# RELEASE NOTES — PhysicsCore V1.0-R5.7.18.2

## Runtime Type-Safe Audit Hotfix

- Fixes detached worker crash `TypeError: sequence item 1: expected str instance, float found`.
- Adds `_safe_join_request_values()` for CAMS ADS request-audit metadata.
- Variable / pressure-level audit serialization now accepts mixed strings, ints, floats, tuples, sets, scalars, and `None`.
- Hardens several evidence/source joins against numeric-like identifiers.
- Streamlit worker monitor now includes the original inner worker traceback in raised diagnostic errors.
- No scientific formula, threshold, Formation/Viewing truth, spectral band, Shared Geometry, or Tier-2 LUT contract changes.
