# R5.7.41.3.4 — Historical GFS AWS Indexed-Range Provider Routing Spec

## Field trigger
2026-08-30 Sunrise / TWS175 historical replay showed that CAMS chains could be recovered, while the frozen GFS 2026-08-29 18Z / f003 native request failed at the NOMADS 0.25° GRIB filter with HTTP 403. The resulting CASE had no native CLWMR/ICMR, therefore Cloud Optics remained Missing and Shadow COT had zero targets.

This is a provider-transport availability problem, not permission to change the model cycle, infer condensate, or reinterpret Missing as Clear.

## Frozen scientific contract
- GFS run/lead resolved by the existing `resolve_run_and_lead()` logic remains frozen.
- Primary native fields remain direct GFS GRIB2 evidence.
- `CLWMR/ICMR` are never synthesized from RH, Cloud Fraction, cloud cover, or Open-Meteo.
- pgrb2b remains diagnostic intermediate-level direct evidence only; it does not independently promote Formation/COT.
- Production/Shadow COT semantics and baseline `R5.7.41.2_SHADOW_COT_AB_FROZEN` are unchanged.

## Transport routing
1. Try the existing NCEP NOMADS GRIB Filter using the frozen run/lead and route bbox.
2. If NOMADS retrieval fails, request the exact same GFS object from NOAA AWS Open Data.
3. Read the public `.idx` sidecar.
4. Select only the requested variable + pressure-level GRIB messages.
5. Convert selected message offsets into complete byte ranges.
6. Download those ranges with HTTP `Range` requests and concatenate complete GRIB2 messages into the local raw cache artifact.
7. Decode with the existing ecCodes route-nearest pipeline; no physics path is forked.

Primary product:
`gfs.YYYYMMDD/HH/atmos/gfs.tHHz.pgrb2.0p25.fFFF`

Secondary Canvas probe:
`gfs.YYYYMMDD/HH/atmos/gfs.tHHz.pgrb2b.0p25.fFFF`

Default AWS source:
`https://noaa-gfs-bdp-pds.s3.amazonaws.com`

## Full-file safety
- Range responses must be HTTP 206.
- HTTP 200 to a range request is rejected before the body is accepted.
- Selected/merged range bytes are bounded by `FIRECLOUD_GFS_AWS_MAX_DOWNLOAD_BYTES`.
- Nearby complete GRIB messages may be merged into bounded spans only as an HTTP optimization; ecCodes still filters the same requested evidence fields.

## Missing policy
If NOMADS and AWS both fail, or the AWS object/index lacks the requested direct native fields, the provider remains failed/Missing. The system must not substitute RH or CF for native condensate.

## Provenance
CASE request audit records:
- NOMADS failure status/error;
- AWS transport selection;
- `.idx` and data object URL;
- selected message count;
- range request count;
- downloaded bytes versus full-object bytes when Content-Length is available.

## Scope
This release does not implement GFS native 127-model-level NetCDF. That remains the later R5.7.42 provider workstream.
