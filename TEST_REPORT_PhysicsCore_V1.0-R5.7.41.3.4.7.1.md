# Test Report — V1.0-R5.7.41.3.4.7.1

## Trigger

Streamlit Cloud startup traceback reached `app.py` top-level import:

`from firecloud.case_archive_stream import write_csv_member_stream`

## Local archive inspection

The delivered R5.7.41.3.4.7 FULL-CLEAN archive contains `firecloud/case_archive_stream.py`, and direct import of `write_csv_member_stream` succeeds locally. Therefore the failure is consistent with deployed source mismatch / stale helper / incomplete file synchronization rather than the canonical archive being unable to import itself.

## Hotfix tests

- Guarded import AST contract: PASS.
- Simulated `ImportError` for `firecloud.case_archive_stream`: PASS.
- Fallback actual CSV write: PASS.
- Fallback payload / SHA256 / byte count exact-equivalence: PASS.
- Canonical stream writer exact CSV payload: PASS.
- R5.7.41.3.4.6 runtime/I-O compatibility: PASS.
- R5.7.41.3.4.7 component profiler compatibility: PASS.

## Full regression

**635/635 PASS**.

One pre-existing pandas FutureWarning remains; no test failure.

## Science impact

None. This hotfix changes deployment/import resilience and CASE export plumbing only.
