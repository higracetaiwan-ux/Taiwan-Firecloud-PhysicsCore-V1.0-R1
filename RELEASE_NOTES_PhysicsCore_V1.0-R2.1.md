# Taiwan Firecloud PhysicsCore V1.0-R2.1

## CASE export hotfix

- Decouples core analysis completion from CASE ZIP generation.
- CASE is generated only when the user presses **產生 CASE ZIP**.
- Streams large DataFrame CSVs directly into ZIP members instead of creating giant intermediate `to_csv()` strings in memory.
- Adds per-file CASE progress and row counts.
- Caches the completed CASE bytes in Streamlit session state so ordinary reruns do not regenerate the archive.
- Preserves the complete evidence CSV/JSON set and ZIP compression level 1.
- Adds `CASE_EXPORT_SERIALIZATION` timing with `COMPUTED_STREAMING`.
- CASE filename now uses `PhysicsCore-V1.0-R2.1`.

This release does not alter R2 physics equations, weights, geometry, or scientific thresholds.
