# Taiwan Firecloud PhysicsCore V1.0-R5.7.14

## Data & CASE Integrity Core

Built from the validated R5.7.13 stable core. This release does **not** continue the R5.7.12 UI/completeness branch.

### Added
- `firecloud/case_integrity.py` evidence-chain guard.
- `analysis_integrity_audit.csv` for provider → decode → route evidence handoff.
- `case_archive_manifest.csv` with per-member row count, uncompressed byte size, and SHA256.
- `case_integrity_audit.csv` for actual archive-member integrity.
- Dependency-aware empty-table handling: target-dependent spectral output may be `ALLOWED_EMPTY` when no canvas candidate exists.
- Hard-fail checks for successful GFS native request followed by empty inventory/completeness, and successful CAMS O3 request followed by missing route evidence.

### Important behavior
- Integrity failure does not block CASE export; the failed CASE remains downloadable for diagnosis.
- Integrity status does not modify Formation, Viewing, Photography Decision, optical thresholds, six-band RT, or Missing semantics.
- No UI consolidation is included.

### Validation
- Full regression: **321 passed / 0 failed**.
- Replayed the validated R5.7.13 2026-09-07 sunset CASE: overall integrity PASS.
- Simulated R5.7.12-style handoff loss: GFS inventory, GFS completeness, and CAMS O3 route handoff correctly become hard FAIL.
