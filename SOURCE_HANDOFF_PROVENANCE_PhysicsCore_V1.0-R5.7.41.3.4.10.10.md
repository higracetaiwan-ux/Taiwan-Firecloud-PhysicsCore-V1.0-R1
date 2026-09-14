# Source Handoff Provenance — V1.0-R5.7.41.3.4.10.10

## Ice Cloud Spectral Optics

首選 calibrated source family：Yang/Bi ice-particle single-scattering database V2。

Raw source columns：

1. wavelength [µm]
2. maximum particle dimension [µm]
3. particle volume [µm³]
4. projected area [µm²]
5. extinction efficiency Qext
6. single-scattering albedo
7. asymmetry factor g

Firecloud normalization：

- six wavelengths：550/575/600/650/700/750 nm
- `D_eff = 1.5 V/A`
- `r_eff_coordinate = D_eff/2`
- `k_ext = Qext A / (rho_ice V)`, `rho_ice=917 kg/m³`
- wavelength interpolation only inside calibrated source grid and must preserve provenance
- no habit interpolation
- effective-radius interpolation only between complete six-band LUT radii, with provenance

No source dataset binary is bundled in the release. A normalized LUT must be built/imported explicitly; this prevents an unverified coefficient table from being mistaken for calibrated physics.
