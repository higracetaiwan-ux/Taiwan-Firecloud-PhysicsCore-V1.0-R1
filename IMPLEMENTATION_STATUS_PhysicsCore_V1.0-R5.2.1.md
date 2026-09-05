# Implementation Status — PhysicsCore V1.0-R5.2.1

Status: implemented and regression-tested.

Implemented:
- Full 0–100 km Earth-shadow / finite-solar-disk penumbra matrix.
- Shared adaptive horizontal sampling: 5 km through 40 km, then 10 km through 100 km.
- 15 distance nodes × 9 core solar-altitude nodes = 135 diagnostic rows.
- Explicit `sampling_step_is_cloud_width=False`.
- Existing per-Canvas F_sun and 650/700/750 nm red-path diagnostics retained.

Scientific boundary:
- H_center is diagnostic, not a hard illumination gate.
- Penumbra is represented by finite solar disk through H_any/H_center/H_full and F_sun.
- Actual red illumination remains dependent on Sun→CloudBase spectral transmission.
