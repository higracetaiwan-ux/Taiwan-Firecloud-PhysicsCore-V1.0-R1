# PhysicsCore V1.0-R5.7.4 Implementation Status

R5.7.4 is a CAMS watchdog/liveness hotfix on top of R5.7.3. Scientific CAMS requests, six-band physics, Formation, Viewing, and Photography Decision formulas are unchanged.

## Fixed
- RUNNING CAMS worker checkpoints no longer read stderr tails. This keeps heartbeat writes non-blocking on mounted filesystems.
- CAMS progress elapsed time is driven by the main scheduler monotonic clock, so the UI cannot remain frozen at a stale `RUNNING 5s / 90s` display merely because a provider callback stops updating.
- Linux deployments add an OS-level `timeout` wrapper around each external CAMS worker as a second watchdog. Exit code 124 is translated to fail-closed `TIMEOUT_DEFERRED`.
- stderr is still captured for terminal FAILED/TIMEOUT diagnostics.

## Scientific invariants
- Missing != Clear != Zero.
- No CAMS timeout is replaced with synthetic O3/aerosol values.
- Formation and Viewing RT remain independent.
- Six wavelengths remain 550/575/600/650/700/750 nm.

## Validation
- 292 tests passed, 0 failed.
