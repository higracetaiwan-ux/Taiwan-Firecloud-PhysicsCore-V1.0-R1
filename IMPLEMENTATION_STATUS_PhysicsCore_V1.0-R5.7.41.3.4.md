# Implementation Status — PhysicsCore V1.0-R5.7.41.3.4

## Implemented
- `firecloud/providers/gfs_aws_range.py`
  - current NOAA GFS AWS object path builder;
  - `.idx` parser;
  - variable/pressure-level message selector;
  - GRIB byte-range planner;
  - bounded range-span merger;
  - HTTP 206/full-file safety guard;
  - atomic local subset assembly and cache provenance.
- `firecloud/providers/gfs_native.py`
  - NOMADS first, AWS indexed-range fallback second;
  - same resolved run/lead preserved;
  - provider audit exposes transport/fallback metadata.
- `firecloud/providers/gfs_canvas_optical_probe.py`
  - identical historical transport fallback for `pgrb2b.0p25`.
- Regression coverage for index parsing, object layout, range-only transfer, HTTP-200 rejection, primary pgrb2 fallback, and pgrb2b fallback.

## Science impact
None. Provider transport only. Missing/direct-evidence rules remain frozen.

## Field validation
Required: rerun 2026-08-30 Sunrise TWS175 after deployment and confirm AWS transport obtains native pgrb2/pgrb2b evidence or fails visibly if the archive object truly does not contain the requested messages.

## Release Gate
CLOSED — working-tree 604/604 PASS；trial fresh-extract 604/604 PASS；final fresh-extract 604/604 PASS；1 個既有 pandas FutureWarning，非失敗。
