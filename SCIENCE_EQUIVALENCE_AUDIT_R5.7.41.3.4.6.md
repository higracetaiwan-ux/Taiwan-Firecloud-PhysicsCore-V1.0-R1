# Science Equivalence Audit — R5.7.41.3.4.6

Baseline compared: `V1.0-R5.7.41.3.4.5` FULL-CLEAN.

## Source-diff boundary

Within the `firecloud/` package, R5.7.41.3.4.6 changes only:

- `firecloud/__init__.py` — version string only;
- `firecloud/case_archive_stream.py` — new non-physical CASE export helper;
- `firecloud/model.py` — DWD API-efficiency summarization + diagnostic aggregation timers only;
- `firecloud/providers/dwd_icon_native.py` — raw-cache transport/provenance/integrity guard only.

All other PhysicsCore science modules are byte-identical to R5.7.41.3.4.5 source package.

## Exact-equivalence evidence

1. DWD cold→warm provider test clears the process-local decoded cache between runs to emulate a new worker. The second run reuses persistent raw bytes, performs zero network requests, and the decoded DataFrame is `check_exact=True` equal to the first run.
2. DWD raw-cache corruption test modifies cached bytes; byte-size/SHA guard rejects the cache and forces redownload.
3. CASE buffered writer tests preserve exact uncompressed CSV bytes, SHA256, byte count and row count.
4. Working-tree full regression: 628/628 PASS, one pre-existing pandas FutureWarning only.
5. Trial fresh-extract full regression: 628/628 PASS, same one pre-existing warning.
6. Final-candidate fresh-extract full regression: 628/628 PASS.
7. Final FULL-CLEAN exact-archive fresh-extract full regression: 628/628 PASS.

## Interpretation

This audit supports engineering/science equivalence for the release boundary. It is not a new Shadow Field Calibration claim. A real R5.7.41.3.4.6 CASE is still useful to measure warm-cache hit rates and the new aggregation profile rows under field runtime conditions.
