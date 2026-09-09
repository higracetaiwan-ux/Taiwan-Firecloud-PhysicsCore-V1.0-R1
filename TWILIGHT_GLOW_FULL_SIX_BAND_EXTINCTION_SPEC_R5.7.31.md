# Twilight Glow Full Six-Band Extinction Spec R5.7.31

## 1. Scope

R5.7.31 only extends the independent Twilight Glow branch:

`Sun → Atmospheric Scatter Volume → Observer`

It does not modify Firecloud Formation (`Sun→CloudBase`), Viewing (`Cloud→Observer`),
Photography Decision, Red-Light Availability, Canvas geometry, 13 solar angles, six-band
wavelengths, route resolution, provider policy, or Forecast/Observation separation.

## 2. Frozen wavelengths

All calculations preserve:

`550 / 575 / 600 / 650 / 700 / 750 nm`

575 nm remains the key O3 Chappuis band. No early reduction to a single red-light score is
allowed.

## 3. Sun → Scatter extinction

For each `time + solar_altitude_deg + glow_volume_id + wavelength`, publish explicit:

- Rayleigh optical depth;
- non-O3 gas optical depth (O2 + H2O);
- O3 optical depth;
- aerosol optical depth;
- cloud optical depth;
- precipitation/hydrometeor optical depth;
- total optical depth;
- transmission;
- incident relative irradiance after finite-solar-disk `DirectSolarFraction`.

The gas total supplied by the existing HITRAN path already contains O3. Therefore the
published non-O3 gas term is `gas_total - gas_O3`; total extinction must never add gas total
and O3 again.

A final Sun-path total/transmission may be published only when all required component
evidence is complete. `DIRECT_EVIDENCE_CONFLICT`, temporal missing aerosol, missing gas,
partial cloud path, or unresolved precipitation must remain partial/missing. No missing
component may be replaced by zero.

## 4. Scatter → Observer extinction

This is a Glow-specific atmospheric path. It is not the existing Cloud→Observer Viewing
result, although it may reuse the same frozen route providers and numerical gas/aerosol/cloud/
precipitation methods.

Publish the same six components plus total tau and transmission. Rayleigh extinction is
explicit. HITRAN gas is independently decomposed into O3 and non-O3 terms while preserving
closure to the frozen Viewing gas total.

## 5. Single-scattering spectral proxy

When both extinction legs, scattering geometry, and local molecular state are complete:

`GlowProxy_λ = Fsun × T_sun→scatter,λ × β_Rayleigh,λ × P_Rayleigh(Θ) × T_scatter→observer,λ`

This is a relative, uncalibrated spectral source proxy. It is not absolute sky radiance.

## 6. Unresolved physics kept explicit

R5.7.31 does not solve:

- aerosol single-scattering albedo;
- aerosol phase function / asymmetry;
- aerosol source scattering term;
- multiple scattering;
- surface/albedo coupling;
- polarization;
- absolute radiometric calibration.

Therefore `calibrated_glow_radiance_available` remains false and the branch remains
`INDEPENDENT_DIAGNOSTIC_ONLY`.

## 7. Required CASE evidence

- `v1_twilight_glow_scattering_volume_550_750nm.csv`
- `v1_twilight_glow_sun_to_scatter_extinction_550_750nm.csv`
- `v1_twilight_glow_scatter_to_observer_extinction_550_750nm.csv`
- `v1_twilight_glow_single_scattering_550_750nm.csv`
- `v1_twilight_glow_summary.csv`

## 8. Integrity requirements

R5.7.31 requires:

- exact Sun-path target coverage;
- exact observer-path target coverage;
- explicit six-band component schema;
- `tau_total = sum(component tau)` closure on Sun path;
- `T = exp(-tau_total)` closure on both paths;
- `incident = Fsun × T_sun` closure;
- single-scattering proxy arithmetic closure;
- partial rows may not publish final total/transmission/proxy;
- no false absolute-radiance claim;
- Glow remains independent from Formation / Viewing / Photography.

## 9. Field acceptance

Code/regression closure is not field closure. A new R5.7.31 deployment CASE must show:

- 13/13 Glow angles;
- full expected atmospheric volume coverage;
- all R5.7.31 Integrity checks PASS;
- Analysis Integrity PASS;
- CASE Integrity PASS;
- no regression in R5.7.29.1 precipitation handoff or Photography 13/13.
