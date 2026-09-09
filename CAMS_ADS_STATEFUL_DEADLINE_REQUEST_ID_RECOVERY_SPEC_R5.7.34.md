# R5.7.34 — CAMS ADS Stateful Deadline / Request-ID Recovery

## Purpose
Remove the flat 90 s ADS wall-clock failure mode without converting provider delay into fabricated data.

## Contract
- Use official `ecmwf-datastores-client` asynchronous submit/get_remote/download workflow.
- Persist opaque ADS request ID plus deterministic dataset/request fingerprint.
- Local timeout never cancels the remote ADS job.
- Next identical role/time/request reattaches to the saved request ID before any new submit.
- A stale/terminal failed remote may be resubmitted; a queued/running remote may not be duplicated.
- Credentials are never persisted in the journal.

## Default deadlines
- Queue/accepted grace: 75 s.
- Running grace: 120 s measured from first running state.
- Total local wait: 180 s.
- External worker hard watchdog: 210 s.

All values are environment-configurable.

## Missing semantics
A deferred local wait remains `TIMEOUT_DEFERRED` / Missing. Spectral AOD, O3 and native 3-D aerosol remain independent provider chains.
