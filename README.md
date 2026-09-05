# Taiwan Firecloud PhysicsCore V1.0

**Current checkpoint: V1.0-R4.3 — Native Condensate Slant RT + Full Optical Path Bridge + Performance Indexing.**

R4.3 retains the shared adaptive horizontal sampling contract (0–40 km: 5 km; 40–100 km: 10 km; 100 km+: 20 km), adds indexed Canvas-specific ray/cloud intersection, CASE diagnostics for native-condensate support, and closes tau_total/transmission only when gas + aerosol + resolved upstream cloud + precipitation optical evidence are all complete. Sampling spacing is never treated as cloud width.

Key boundary: target-cloud vertical COT can be derived from native condensate using an explicit geometric-optics model with assumed effective radii. Upstream slant cloud optical depth is **not** fabricated from isolated route columns; it remains unresolved until native horizontal/3-D support is available.

Six-band and Missing semantics from R3.x/R4 remain unchanged. 550-nm gas spectroscopy remains fail-closed until a verified six-band gas LUT is installed.

See `RELEASE_NOTES_PhysicsCore_V1.0-R4.3.md`.
