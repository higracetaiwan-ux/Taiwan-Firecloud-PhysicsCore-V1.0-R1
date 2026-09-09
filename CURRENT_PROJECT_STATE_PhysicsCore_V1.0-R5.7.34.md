# Taiwan Firecloud PhysicsCore — Current Project State V1.0-R5.7.34

Current production candidate: `Taiwan Firecloud PhysicsCore V1.0-R5.7.34`.

## R5.7.34
CAMS ADS Stateful Deadline / Request-ID Recovery is code-complete. The flat 90 s ADS wait is replaced by separate queue/running/total local wait deadlines. Opaque ADS request IDs are persisted with request fingerprints and identical later requests reattach before submitting new jobs. Remote provider Missing remains Missing.

## Frozen science
Formation / Viewing / Twilight Glow remain independent. Runtime angles remain 0 to -6 degrees in 0.5-degree steps. Six wavelengths remain 550/575/600/650/700/750 nm. Missing != Clear != Zero != N/A.

## Next
After R5.7.34 regression/package closure, proceed to Aerosol Scattering Physics (SSA / phase function) as a separate science release.
