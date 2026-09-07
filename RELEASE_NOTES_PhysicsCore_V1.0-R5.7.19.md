# RELEASE NOTES — PhysicsCore V1.0-R5.7.19

## Calibrated Scattering LUT Ingestion + Interpolation-Domain Contract

- Adds `firecloud/tier2_scattering_runtime.py` for validated LUT resolve/load/install.
- A runtime LUT now requires a paired manifest with calibration ID/source/date, frozen six-band declaration, supported phases, LUT version, and exact CSV SHA256.
- Adds `firecloud/tier2_scattering_domain.py` for per-target interpolation-domain auditing.
- Exact target: deterministic interpolation-domain eligibility only when all required local cells are complete.
- Bounded target: bounded eligibility only; the full COT interval must remain inside complete local cells.
- Conflict/unknown COT: remains blocked before LUT interpolation.
- Scattering angle is never clamped to the LUT domain; out-of-domain is explicit.
- Missing local grid corners produce `LUT_LOCAL_CELL_INCOMPLETE` even when global min/max ranges contain the target.
- No calibrated LUT is bundled and no production Tier-2 response interpolation is executed in R5.7.19.
- Adds CASE exports `v1_tier2_scattering_lut_audit.csv`, `v1_tier2_scattering_lut_domain.csv`, and `v1_tier2_scattering_lut_domain_summary.csv`.
- Adds CLI installer `tools/install_tier2_scattering_lut.py` and Streamlit-secret path bridging without adding new scientific UI behavior.
