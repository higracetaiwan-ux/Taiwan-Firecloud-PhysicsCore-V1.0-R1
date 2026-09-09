# Taiwan Firecloud PhysicsCore V1.0-R5.7.30.1 Release Notes

## Integrity Regression Restore + Packaging Continuity Hotfix

During review of R5.7.30, the new Twilight Glow branch passed its own tests, but
an unrelated regression was found in the already field-validated R5.7.29.1
Viewing precipitation Integrity contract. Two strict guards had been replaced by
a weaker check that only required a non-empty downstream table.

R5.7.30.1 restores:

- `VIEWING_PRECIPITATION_TARGET_COVERAGE`;
- `VIEWING_NATIVE_HYDROMETEOR_HANDOFF`;
- hard failure for partial target coverage when native hydrometeors are READY;
- hard failure for `VIEW_PRECIPITATION_VOLUME_UNRESOLVED` under native-ready evidence;
- the R5.7.29.1 versioned release notes and spool-handoff specification in the
  FULL-CLEAN replacement package.

R5.7.30 Twilight Glow remains unchanged. No scientific weights, Formation,
Viewing extinction equations, Photography logic, angles, wavelengths, route
resolution or provider policy are changed.

## Verification

- R5.7.29 + R5.7.30 + R5.7.30.1 focused regression: 15 passed / 0 failed;
- full working-tree regression: 482 passed / 0 failed.
