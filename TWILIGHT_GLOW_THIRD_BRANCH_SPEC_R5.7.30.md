# Twilight Glow Third Branch Specification — R5.7.30

## 1. Branch identity

The branch is an independent diagnostic path:

`Sun → atmospheric scatter volume → Observer`

It is neither the Formation path (`Sun → CloudBase`) nor the Viewing path
(`Cloud → Observer`). It cannot create a Canvas, alter `formation_state`, or
modify `photography_opportunity`.

## 2. Domain and bands

- Runtime timeline: the frozen 13 solar-altitude angles from 0° through −6°.
- Atmospheric volumes: the existing forward reference domain at 10, 20, 30,
  40, 60, 80 and 100 km, three direction offsets, and nominal 4, 5, 8 and
  12 km altitude levels.
- Spectral bands: 550, 575, 600, 650, 700 and 750 nm.
- Identity key: `time + solar_altitude_deg + glow_volume_id`.

## 3. Resolved physics

For each atmospheric volume and wavelength, R5.7.30 preserves:

1. the relative incident irradiance from the existing Red-Light reference
   Sun path;
2. non-Rayleigh observer-path optical depth from gas, CAMS aerosol, cloud and
   forecast-native precipitation;
3. observer-path Rayleigh optical depth integrated from pressure and
   temperature profiles;
4. local molecular number density and a Rayleigh scattering cross-section
   consistent with the existing six-band Rayleigh optical-depth convention;
5. the normalized unpolarized Rayleigh phase function;
6. an uncalibrated single-scattering source proxy:

   `incident × exp(−observer_total_tau) × molecular_scattering_coefficient × phase_function`.

All required evidence must be Full before final total optical depth,
transmission or source proxy is populated.

## 4. Explicitly unresolved physics

R5.7.30 does not infer aerosol source scattering from AOD or relative humidity.
Aerosol single-scattering albedo and phase function are unavailable. Calibrated
angular-volume integration and multiple scattering are also unavailable.
Therefore `calibrated_glow_radiance_available` is always false and the product
must not be interpreted as absolute sky radiance, luminance, colour, a Glow
probability, or a photographic decision.

## 5. Evidence and archive contract

CASE archives must include:

- `v1_twilight_glow_scattering_volume_550_750nm.csv`
- `v1_twilight_glow_summary.csv`

Analysis Integrity must hard-check:

- 13-angle coverage shared with Formation;
- unique time/angle/volume keys;
- explicit six-band schema;
- transmission and source-proxy arithmetic closure;
- branch independence from Formation/Photography;
- absence of a false calibrated-radiance claim.

Missing is never converted to zero, Clear, Blocked or Not Applicable.
