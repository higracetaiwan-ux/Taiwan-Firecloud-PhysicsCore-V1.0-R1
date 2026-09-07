# Tier-2 Scattering Runtime — R5.7.20

No calibrated scattering LUT is bundled with PhysicsCore.

Install a validated pair using:

`python tools/install_tier2_scattering_lut.py <lut.csv> <manifest.json>`

or point the deployment to an external validated pair with:

- `FIRECLOUD_TIER2_SCATTERING_LUT_PATH`
- `FIRECLOUD_TIER2_SCATTERING_LUT_MANIFEST_PATH`

R5.7.20 has two gates:

1. R5.7.19 ingestion/domain validity (`audit.ok`)
2. R5.7.20 production calibration validity (`audit.solver_eligible`)

Legacy/synthetic R5.7.19 manifests may remain useful for regression-domain tests but cannot execute the production Tier-2 interpolation solver. A missing LUT is a valid operational state and never triggers synthetic response.
