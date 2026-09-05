# Taiwan Firecloud PhysicsCore V1.0-R4.8.2

## Narrow-band 550 nm builder performance release

- Keeps the validated 360-row 575/600/650/700/750 nm Runtime LUT and computes only the missing 550 nm states.
- Before the 48 H2O/O2 Voigt T/P states, creates an in-memory HAPI source table filtered to the 550 nm output interval plus a conservative 200 cm-1 transition-center margin.
- The output 550 nm band remains 537.5–562.5 nm and the configured 0.02 cm-1 output grid is unchanged.
- If HAPI table filtering is unavailable or fails, the builder falls back to the original full source table rather than changing physical semantics.
- Adds per-state elapsed/average/ETA progress messages and exposes them in the Streamlit status panel.
- O3 remains the measured Serdyuchenko–Gorshelev XSC branch; no 550 nm interpolation is introduced.
- No PhysicsCore weights, gates, Formation semantics, or six-band contracts were changed.
