# Taiwan Firecloud PhysicsCore V1.0-R5.7.4

## CAMS watchdog hotfix
R5.7.3 could appear permanently stuck at `NATIVE_AEROSOL_532NM_PRESSURE_LEVEL:RUNNING 5s / 90s` if the heartbeat/checkpoint path itself stopped advancing. R5.7.4 separates user-visible elapsed time from provider callback cadence and removes log-tail reads from RUNNING heartbeat writes.

### Changes
- scheduler-clock CAMS elapsed display;
- non-blocking RUNNING checkpoint;
- OS-level worker deadline fallback on Linux;
- exit 124 -> `TIMEOUT_DEFERRED`;
- terminal stderr/PID/exit-code diagnostics retained.

No scientific thresholds, CAMS variables, optical equations, Formation/Viewing separation, or Photography Decision logic changed.

Tests: 292 passed / 0 failed.
