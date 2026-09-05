# Taiwan Firecloud PhysicsCore V1.0

**Current checkpoint: V1.0-R4.2 — Shared Adaptive Horizontal Sampling + Native 3D Slant Blocker RT.**

R4.2 adds one shared adaptive horizontal sampling contract (0–40 km: 5 km; 40–100 km: 10 km; 100 km+: 20 km) and derives upstream slant cloud optical depth only where adjacent native-condensate columns establish auditable horizontal support. Sampling spacing is never treated as cloud width. R4.1 native condensate/COT safeguards remain unchanged.

Key boundary: target-cloud vertical COT can be derived from native condensate using an explicit geometric-optics model with assumed effective radii. Upstream slant cloud optical depth is **not** fabricated from isolated route columns; it remains unresolved until native horizontal/3-D support is available.

Six-band and Missing semantics from R3.x/R4 remain unchanged. 550-nm gas spectroscopy remains fail-closed until a verified six-band gas LUT is installed.

See `RELEASE_NOTES_PhysicsCore_V1.0-R4.2.md`.
