# Taiwan Firecloud PhysicsCore V1.0-R4.7.1

Runtime hotfix for R4.7.

- Added the missing `from pathlib import Path` import in `firecloud/model.py`.
- Fixes `NameError: name 'Path' is not defined` while building `v1_six_band_spectroscopy_readiness`.
- No physics equations, thresholds, weights, RT semantics, provider logic, or Stage 1–9 contracts were changed.
