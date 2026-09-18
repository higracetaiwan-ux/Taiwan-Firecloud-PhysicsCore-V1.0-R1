# Step 3P Full-Spectral Source Qualification Design

## Goal
Qualify whether the authoritative Yang/Bi V2 396-wavelength source bytes required for RRTMG band-24/band-25 integration are actually available and spectrally covering the target bands, without inventing spectral weights or promoting production ice optics.

## Frozen boundaries
- Science baseline remains `R5.7.41.2_SHADOW_COT_AB_FROZEN`.
- Portable six-band LUT is not expanded/interpolated into a synthetic spectrum.
- Only `single_column` and `Rough000/Rough003/Rough050` are inspected.
- Exact Fu96/RRTMG band weighting remains unavailable until separately proven.
- Independent SSA/g validation, six-band exact validation, `tau_ice` production and physics promotion remain false.

## Runtime behavior
The release can run without the large Yang/Bi source archive. In that state the qualification must emit deterministic fail-closed evidence with `SOURCE_BYTES_UNAVAILABLE`. If a source root is supplied, the module resolves and inspects the three authoritative `isca.dat` files and reports source-domain coverage for RRTMG SW bands 24 and 25.
