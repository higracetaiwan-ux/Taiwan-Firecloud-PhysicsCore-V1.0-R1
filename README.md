# Taiwan Firecloud PhysicsCore V1.0

**Current checkpoint: V1.0-R4.4 — Cloud Optical Validation + Six-band Spectral Color Foundation.**

R4.4 builds on R4.3 without changing frozen causality. It adds a formal cloud-optical validation table that distinguishes condensate-positive/slant-RT-validated cases from Missing condensate baselines, and adds a six-band human-visible colour diagnostic foundation using only 550/575/600/650/700/750 nm radiance.

The colour reconstruction is deliberately fail-closed: no blue or blue-green wavelength is invented, 550 nm is never back-filled from 575/600 nm, and CIE XYZ/x/y outputs are explicitly labelled as **truncated retained-band diagnostics**, not a complete broadband human-visible spectrum. Brightness, Redness and Effective Illuminated Area remain separate Formation dimensions; there is no Formation Score.

R4.4 preserves the shared adaptive horizontal sampling contract (0–40 km: 5 km; 40–100 km: 10 km; 100 km+: 20 km), native-condensate multi-column support, and resolved slant blocker RT from R4.3. Sampling spacing is never treated as cloud width.

Important validation behavior:
- native condensate/COT present + resolved multi-column support + resolved slant intersection → `CONDENSATE_POSITIVE_SLANT_RT_VALIDATED`;
- condensate present but support unresolved → `CONDENSATE_POSITIVE_HORIZONTAL_SUPPORT_NOT_RESOLVED`;
- no native condensate optical evidence → `NO_NATIVE_CONDENSATE_OPTICAL_EVIDENCE`.

550-nm gas spectroscopy remains fail-closed until a verified six-band H2O/O2/O3 Runtime LUT is installed.

See `RELEASE_NOTES_PhysicsCore_V1.0-R4.4.md`.
