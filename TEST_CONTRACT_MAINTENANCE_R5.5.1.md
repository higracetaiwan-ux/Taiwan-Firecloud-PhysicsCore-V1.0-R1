# PhysicsCore V1.0-R5.5.1 Test Contract Maintenance

This maintenance pass updates legacy regression tests to the current PhysicsCore contract without changing scientific runtime behaviour.

## Changes
- Cloud optical-path unresolved transmission is asserted as Missing/NaN, not clear/1.0.
- CAMS subprocess IPC test checks the current file-backed atomic subprocess contract instead of a TemporaryDirectory implementation detail.
- Legacy V8.x version-string assertions now target Taiwan Firecloud PhysicsCore V1.0 / R5.x runtime naming.
- HITRAN derived-LUT manifest tests now assert the retained PhysicsCore-V1.0-R4.8.2 science-grid schema independently of runtime release version.
- HITRAN progress/resume tests now assert current FC_PROGRESS and VOIGT_STATE_CACHE_HIT instrumentation.
- CASE filename/UI tests now assert the current PhysicsCore naming family.

## Regression result
- 269 passed
- 0 failed

No production science logic was changed in this maintenance pass.
