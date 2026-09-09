# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.34

## Theme
CAMS ADS Stateful Deadline / Request-ID Recovery.

## Changes
- Added `firecloud/providers/cams_ads_stateful.py`.
- Added durable request-ID journal keyed by request fingerprint.
- Added queue/running/total phased deadlines.
- Added same-request reattach via `get_remote(request_id)`.
- Local defer no longer implies remote cancellation or immediate duplicate request.
- Explicit dependency: `ecmwf-datastores-client>=0.5.3`.
- External worker watchdog default raised from 90 s to 210 s as a final safety ceiling; stateful local waits remain bounded at 180 s by default.

## Science
No Formation, Viewing, Glow, six-band, angle, Canvas, aerosol optics or Photography science changes.
