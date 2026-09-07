# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.21

## Cross-Region Timezone + UTC Physics Contract

### Purpose
R5.7.21 closes the cross-region event-time ambiguity exposed by the 2026-09-08 Japan REAL_CANVAS regression CASE. Earlier UI requests always wrote `Asia/Taipei`, even when the test coordinates were in Japan. That did not necessarily move the sunset crossing by a full hour, but it made CASE civil-time provenance incorrect and the NOAA fractional-year implementation could change solar state slightly when the same instant was represented in another timezone.

### Changes
- Added `firecloud/timezone_contract.py`.
- Coordinate-aware IANA timezone resolution:
  - `timezonefinder` when available.
  - deterministic Taiwan / western-Japan / Ryukyu fallback.
  - longitude-derived fixed-offset fallback instead of silently assuming Taiwan.
- Added explicit timezone modes:
  - `AUTO_COORDINATE`
  - `USER_OVERRIDE`
- Manual overrides are never silently rewritten. A coordinate/override mismatch produces a persisted warning.
- Solar declination/equation-of-time and true-solar-time calculations now canonicalize the physical instant to UTC.
- The same instant represented in UTC / Asia/Taipei / Asia/Tokyo produces identical solar elevation and azimuth.
- Streamlit sidebar now exposes timezone source and optional manual IANA override.
- Analysis worker receives `tz_mode` and effective timezone explicitly.
- `summary.csv` adds `time_utc`, `event_timezone`, and `timezone_mode`.
- CASE adds:
  - `event_time_contract.csv`
  - `event_timezone_resolution.json`
- `event_time_contract.csv` records local civil time, UTC time, UTC offset, resolver source, override provenance, mismatch state, event local date, and event kind for every solar altitude.
- Added `timezonefinder>=6.5` to deployment requirements. Runtime remains safe if the optional import fails because deterministic fallbacks remain available.

### Science boundary
This release changes time/provenance handling only. It does **not** change:
- Formation vs Viewing separation,
- six-band spectral physics,
- Target Optical Truth,
- Tier-1 response,
- Tier-2 readiness/foundation/domain/solver mathematics,
- calibrated-LUT production gate,
- photography decision thresholds.

### Validation
- Cross-region timezone tests: Japan coordinate resolves to Asia/Tokyo; Taiwan coordinate resolves to Asia/Taipei.
- Manual mismatch test: Japan coordinates + Asia/Taipei override remains Asia/Taipei with explicit warning.
- UTC invariance test: identical solar geometry for the same physical instant represented in three timezones.
- Event crossing test: Tokyo/Taipei civil clock labels differ while resolving the same physical sunset instant.
- Full regression: **370 passed / 0 failed**.
