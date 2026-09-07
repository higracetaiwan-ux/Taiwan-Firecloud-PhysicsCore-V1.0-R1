# Tier-2 Scattering Runtime

No calibrated scattering LUT is bundled with PhysicsCore R5.7.19.

Install a validated pair here using:

`python tools/install_tier2_scattering_lut.py <lut.csv> <manifest.json>`

or point the deployment to an external validated pair with:

- `FIRECLOUD_TIER2_SCATTERING_LUT_PATH`
- `FIRECLOUD_TIER2_SCATTERING_LUT_MANIFEST_PATH`

A missing LUT is a valid operational state and never triggers synthetic Tier-2 response.
