# Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.1

## Changes
- Retains R5.7.41.3.4 Historical GFS AWS indexed-range fallback for pgrb2/pgrb2b.
- Fixes a false Analysis Integrity failure when Glow cloud provenance is explicitly `GLOW_OBSERVER_CLOUD_EVIDENCE_MISSING`.
- Explicit Missing remains Missing; no cloud tau is synthesized and no clear-sky promotion is allowed.

## Field evidence
- Triggered by R5.7.41.3.3 historical replay: 2026-08-30 sunrise, TWS175.


## Release Gate
- Working-tree nodeid coverage: **605/605 PASS**
- Trial fresh-extract nodeid coverage: **605/605 PASS**
- Existing pandas FutureWarning: 1 (non-failure)
- Release Gate: CLOSED
