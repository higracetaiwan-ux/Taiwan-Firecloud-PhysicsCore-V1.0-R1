# Taiwan Firecloud PhysicsCore V1.0-R5.5 Release Notes

## R5.5 — Secondary Native Optics Live Chain

R5.5 closes the main engineering gap left in R5.0–R5.4: the secondary Target-Canvas optical-evidence path is no longer limited to a local ECMWF IFS GRIB contract.

### Provider priority

1. **ECMWF IFS native cloud microphysics** when an entitled/local model-level GRIB is explicitly configured.
2. **DWD ICON Global Open Data** as the public network fallback.

ECMWF Open Data itself is not used as a substitute for model-level CLWC/CIWC because its public subset does not expose those fields. R5.5 therefore keeps the IFS local/entitled path and adds DWD ICON Global model-level native QC/QI.

### DWD ICON Global native optical bridge

The provider reads forecast-native:

- QC — specific cloud liquid water content
- QI — specific cloud ice content
- T — temperature
- P — pressure
- FI — geopotential / model-level geometry

The fetch is two-stage:

1. probe QC/QI on ICON Global model levels 55–108 (configurable),
2. only for condensate-positive levels, fetch T/P/FI and derive layer geometry and COT.

This prevents downloading all large thermodynamic fields when no usable target condensate exists.

### Physics rules preserved

R5.5 still forbids:

- Cloud Fraction → COT
- RH → COT
- geometry → COT
- satellite observation → forecast COT
- surface rain rate → precipitation optical depth

A secondary record is eligible only as `FORECAST_MODEL_NATIVE_OPTICS` with finite native-condensate-derived COT and explicit provenance.

### Runtime/cache

- persistent DWD GRIB cache under `.firecloud_cache/dwd_icon_secondary` by default,
- process-level run/lead/route cache,
- parallel condensate probing,
- configurable network timeout/workers/model levels.

Environment controls:

- `FIRECLOUD_DWD_ICON_SECONDARY_ENABLED=1|0`
- `FIRECLOUD_DWD_ICON_CACHE_DIR=...`
- `FIRECLOUD_DWD_ICON_TIMEOUT_S=20`
- `FIRECLOUD_DWD_ICON_WORKERS=8`
- `FIRECLOUD_DWD_ICON_MODEL_LEVELS=55-108`

### CASE evidence

New CASE audit files:

- `dwd_icon_request_audit.csv`
- `secondary_provider_audit.csv`

Existing:

- `ecmwf_ifs_request_audit.csv`
- `v1_secondary_target_optics.csv`
- `v1_target_canvas_optical_evidence.csv`

### Tests

Focused R5.5 + secondary-arbitration + R5.4 red-window tests: **12 passed**.

Full suite: **256 passed, 10 known stale/legacy failures**. No new R5.5 regression failure was introduced.

### Validation status

The live DWD URL/filename contract and official model-variable availability were verified against DWD public Open Data documentation/indexes. The execution environment used to build this release does not provide outbound DNS/network access, therefore a real DWD GRIB download could not be executed here. The next user-run CASE is the operational validation of the network chain.
