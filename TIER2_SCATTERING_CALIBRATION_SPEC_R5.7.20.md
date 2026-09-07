# Taiwan Firecloud Tier-2 Scattering Calibration Specification — R5.7.20

## Purpose

Freeze the software/physics interface for target-cloud scattering without pretending that a calibration dataset exists before it has been produced and validated.

## Response definition

For each frozen wavelength λ:

`response_factor_λ = target directional radiance_λ / cloud-base incident irradiance_λ`

Units: `sr^-1`.

The LUT represents target-cloud optical response only. Sun→CloudBase gas/aerosol/cloud-path transmission is already contained in `E_base,λ` and must not be baked into the LUT a second time.

## Independent LUT coordinates

- phase: LIQUID / ICE (MIXED only with explicit validated calibration)
- wavelength: 550, 575, 600, 650, 700, 750 nm
- target COT
- effective radius `r_eff`
- cloud geometric thickness `Δz`
- Sun→Cloud→Observer scattering angle

Scattering angle convention: 0° forward scattering, 180° backward scattering.

## External RT requirement

Production samples must come from a physically based, versioned radiative-transfer solver with multiple scattering enabled. The manifest must identify the solver, cloud optical-property source, phase-function source and validation reference.

The software supports validated libRadtran/uvspec + DISORT or MYSTIC workflows and other explicitly validated external DISORT/Monte-Carlo solvers. PhysicsCore itself does not run or emulate those solvers in the operational analysis path.

## Water clouds

The calibration metadata must declare the water-droplet optical-property source. Mie-based optical properties are suitable only when the exact refractive-index/size-distribution/table provenance is frozen and validated.

## Ice clouds

The calibration metadata must declare the ice-crystal optical-property / phase-function parameterization and its source. Liquid-cloud Mie behavior must never be reused for ice clouds.

## Grid and interpolation

Production package build requires a complete Cartesian 4-D tensor per phase × wavelength. The runtime separately verifies the local interpolation cell around each target.

No extrapolation or clamping is allowed. Out-of-domain remains explicit.

## Calibration QA

A package cannot become production solver eligible until:

- all external RT jobs are complete;
- response values are finite/nonnegative;
- the tensor grid is complete;
- solver/optical provenance is complete;
- QC state is PASS;
- a validation reference is recorded;
- CSV SHA256 matches the manifest.

## Operational separation

Tier-2 remains an independent evidence branch in R5.7.20. It does not overwrite Tier-1 or Formation. A later architecture-freeze release may decide how validated Tier-2 response participates in final Formation Brightness/Redness/Effective Area, but only after real calibrated-LUT event validation.
