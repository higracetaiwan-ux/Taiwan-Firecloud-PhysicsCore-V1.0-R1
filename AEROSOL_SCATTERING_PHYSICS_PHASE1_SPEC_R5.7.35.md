# Twilight Glow Aerosol Scattering Physics Phase 1 — R5.7.35

## Scope
R5.7.35 adds an independent aerosol single-scattering source branch to Twilight Glow. It does not alter Firecloud Formation, Viewing, Photography Decision, Canvas rules, solar-angle sampling, or the six-band contract.

## Native CAMS evidence
A new CAMS role `AEROSOL_SCATTERING_COLUMN_PROPERTIES` requests, at one forecast valid time and one frozen route bbox:

- total aerosol optical depth: 532/550/645/670/800 nm
- single-scattering albedo: 550/645/670/800 nm
- asymmetry factor: 550/645/670/800 nm

These are provider-native column optical properties. They are not interpreted as a vertical profile.

## Vertical extinction
The local 3-D extinction anchor remains native CAMS pressure-level aerosol extinction at 532 nm:

`beta_ext,lambda(z) = beta_ext,532,native3D(z) * AOD_lambda / AOD_532`

If native 3-D extinction or AOD532 is missing, the aerosol source remains Missing. If AOD532 is zero while native 3-D extinction is positive, the state is an explicit direct-evidence conflict.

## Six-band interpolation
PhysicsCore wavelengths remain 550/575/600/650/700/750 nm.

- AOD: exact native wavelength or bounded log-log interpolation only.
- SSA: exact native wavelength or bounded linear interpolation only.
- asymmetry g: exact native wavelength or bounded linear interpolation only.
- no wavelength extrapolation is permitted.

## Phase function
Phase 1 uses the normalized Henyey-Greenstein approximation driven by provider-native asymmetry `g`:

`P_HG(theta,g) = (1-g^2) / [4*pi*(1+g^2-2g*cos(theta))^(3/2)]`

This is explicitly labeled `HENYEY_GREENSTEIN_FROM_NATIVE_ASYMMETRY_FACTOR`; it is not claimed to be the full native aerosol phase function.

## Single-scattering source
For each band:

- `beta_sca = beta_ext * SSA`
- `beta_source = beta_sca * P_HG`
- `AerosolProxy = E_incident * T_observer * beta_source`
- `CombinedProxy = RayleighProxy + AerosolProxy` only when both components are complete.

## Missing semantics
Missing != Clear != Zero != N/A.
No fixed SSA, fixed g, fixed Angstrom exponent, RH-derived aerosol, or synthetic AOD is introduced.

## Radiance claim
`calibrated_glow_radiance_available = False` remains frozen. R5.7.35 is a relative single-scattering source proxy only. Multiple scattering and absolute radiometric calibration remain open.
