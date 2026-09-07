# Taiwan Firecloud PhysicsCore V1.0-R5.7.21

## R5.7.21 Cross-Region Timezone + UTC Physics Contract

R5.7.21 makes event time semantics coordinate-aware for cross-region PhysicsCore regression testing. The local civil timezone is resolved from coordinates (global IANA resolution through optional/runtime `timezonefinder`, with deterministic Taiwan/Japan/fixed-offset fallbacks), while solar physics is canonicalized to UTC so the same physical instant produces identical solar elevation/azimuth regardless of whether it is represented in Asia/Taipei, Asia/Tokyo, or UTC.

The Streamlit event request now stores timezone mode, coordinate-resolved timezone, effective timezone, resolver provenance, and mismatch warnings. Manual IANA timezone overrides are preserved rather than silently rewritten. CASE export adds `event_time_contract.csv` and `event_timezone_resolution.json`, explicitly pairing local civil event times with their UTC instants for every solar-altitude checkpoint.

The R5.7.20 Tier-2 calibration/solver chain is unchanged. No physical thresholds, Formation/Viewing semantics, target optical truth, or LUT production gates are altered.

---

# Taiwan Firecloud PhysicsCore V1.0-R5.7.20

## R5.7.20 Calibrated Scattering Solver + Calibration Package Contract

R5.7.20 completes the executable Tier-2 scattering software path while keeping production physics gated behind an externally generated and validated calibrated LUT. It adds a production calibration-package contract, explicit external RT job generation, strict calibration provenance/QC checks, one immutable prepared LUT index per event, and six-band 4-D multilinear interpolation. Exact target truth may produce deterministic Tier-2 evidence; bounded COT produces interval-only evidence; conflict/unknown targets remain blocked. Tier-2 is still independent of Formation/Photography Decision in this release.

No production calibrated LUT is bundled. A schema-valid R5.7.19 LUT without the R5.7.20 production calibration contract remains usable for domain regression but cannot execute the solver. CASE export adds `v1_tier2_scattering_response_550_750nm.csv` and `v1_tier2_scattering_response_summary.csv`. Genuine NO_CANVAS events now also preserve a fixed schema in `v1_canvas_candidates.csv`.

## R5.7.19 Calibrated Scattering LUT Ingestion + Interpolation-Domain Contract

R5.7.19 continues from the accepted R5.7.18.2 runtime hotfix. It adds strict calibrated Tier-2 scattering LUT runtime ingestion, manifest/SHA256/calibration provenance validation, and per-target interpolation-domain evidence. Production Tier-2 radiance interpolation is still disabled.

A target is not considered interpolation-ready merely because it falls between global LUT minima and maxima. For the frozen six bands (550/575/600/650/700/750 nm), R5.7.19 requires a complete local four-dimensional interpolation cell in `COT × effective radius × cloud thickness × scattering angle` for the target phase. Exact optical truth may reach deterministic domain eligibility; bounded truth may reach bounded domain eligibility only when the complete COT interval is covered. Conflict/unknown optical truth remains blocked.

Runtime LUT installation requires both a CSV and a calibrated provenance manifest with matching SHA256. No calibrated LUT is bundled in this release, so a default deployment remains safely in `CALIBRATED_LUT_NOT_INSTALLED` rather than generating synthetic Tier-2 response. CASE export adds `v1_tier2_scattering_lut_audit.csv`, `v1_tier2_scattering_lut_domain.csv`, and `v1_tier2_scattering_lut_domain_summary.csv`.

## R5.7.18.2 Runtime Type-Safe Audit Hotfix

R5.7.18.2 is a narrow runtime reliability hotfix on top of R5.7.18.1. It does not change Formation, Viewing, Tier-1/Tier-2 physics, Shared Geometry, or integrity thresholds. It hardens provider request-audit metadata serialization so mixed numeric/string ADS metadata cannot crash the detached analysis worker. It also surfaces the preserved inner worker traceback through the Streamlit monitor when a future worker failure occurs.

## R5.7.18.1 Spectral Evidence Payload Integrity

R5.7.18.1 is a narrow integrity hardening release on top of R5.7.18. It does not change Formation, Viewing, Tier-1 response, scattering geometry, or the Tier-2 LUT foundation. The release extends the Data/CASE Integrity contract from table/row existence to payload validity.

New payload-level checks include CAMS request-audit presence when CAMS-dependent evidence is expected, numeric O3 payload coverage, O3 quality-missing fraction, core gas payload coverage, and spectral aerosol payload coverage. A table with rows but all O3 values missing is now a hard integrity failure; a valid provider/payload case remains PASS.

## R5.7.18 Tier-2 Scattering LUT / Solver Foundation

R5.7.18 continues directly from R5.7.17. It adds the physically required Sun→Cloud→Observer scattering-angle geometry and a strict six-band calibrated-LUT contract. No calibrated LUT is bundled and production Tier-2 interpolation/radiance remains disabled; therefore R5.7.18 cannot fabricate a Tier-2 response merely because target inputs are complete.

## R5.7.17 Tier-2 Scattering Readiness Contract

R5.7.17 continues directly from the user-selected R5.7.16 Target Cloud Optical Response Tier-1 Closure baseline. It adds a target-by-target Tier-2 readiness truth layer only; no Tier-2 scattering solver, LUT multiplier, Mie approximation, or multiple-scattering response is enabled in this release.

Each Canvas target now records independent readiness for COT truth (exact / bounded / conflict / missing), phase, effective radius, geometric thickness, and six-band incident illumination. Even when all inputs are present, the strongest allowed state in this release is `INPUTS_READY_AWAITING_LUT_SOLVER`, because the calibrated scattering LUT/solver is intentionally not frozen yet. Conflict/unknown COT cannot be rescued by Cloud Fraction, RH, phase, or r_eff.

CASE export adds `v1_tier2_scattering_readiness.csv` and `v1_tier2_scattering_readiness_summary.csv`. Formation, Viewing, six-band Tier-1 response, thresholds, Shared Geometry, and UI decision logic are unchanged.


Current operational focus: **Data & CASE Integrity Core**, built on the R5.7.13 Shared Geometry Phase-1 baseline. No scientific thresholds, Formation/Viewing formulas, or UI semantics are changed in this release.

# Taiwan Firecloud PhysicsCore V1.0-R5.7.13


R5.7.13 operational focus: Firecloud Shared Geometry Core V1.5 Phase-1 Completion, rebuilt from the proven R5.7.11 stable baseline (not from the regressed R5.7.12 branch). Canonical geometry now includes Earth curvature/great-circle routing, WGS84 geodetic↔ECEF↔ENU transforms, ray–sphere intersection, Sun→CloudBase and Cloud→Observer ray primitives, finite-solar-disk/penumbra geometry, shared voxel topology/intersection plans, canonical vertical indexing/layer bounds, and cross-angle ray-matrix reuse. Formation, Viewing, cloud blocking, precipitation and gas RT consume the same geometry source-of-truth. No UI/completeness redesign and no scientific thresholds/weights are changed.

R5.7 continues from the verified R5.6.1 baseline. It keeps Formation, Viewing and Photography Decision physically separate while adding forecast-native 3-D hydrometeor optics and an independent Cloud→Observer six-band extinction branch.

## R5.7 additions

- GFS native RWMR / SNMR / GRLE hydrometeor fields are requested and preserved as 3-D forecast evidence. Surface rain rate is never converted to optical depth.
- Sun→CloudBase precipitation optical depth is integrated from native hydrometeor volume with an explicit large-particle visible-band Tier-1 optical model.
- Cloud→Observer precipitation extinction is integrated independently along the viewing ray.
- Viewing geometry uses angular-footprint projected cloud volumes and continuous cloud-fraction interpolation only across vertically continuous adjacent forecast nodes.
- Cloud→Observer six-band gas / aerosol / cloud / precipitation diagnostics are exported separately from Formation RT. No Sun→CloudBase transmission is reused.
- Photography Decision receives Viewing spectral readiness as a diagnostic only; no uncalibrated spectral threshold rewrites Formation or the geometry decision.
- Full Six-Band Formation closure now has a forecast-native precipitation path source when native hydrometeor volume is available. Remaining Missing components stay Missing.

Core invariants remain frozen: Formation != Viewing != Glow; Penumbra Geometry != Spectral RT; Missing != Clear != Zero; Cloud Fraction != COT; Satellite Observation != Forecast Input; Brightness != Redness != Effective Illuminated Area.

See `RELEASE_NOTES_PhysicsCore_V1.0-R5.7.md` and `IMPLEMENTATION_STATUS_PhysicsCore_V1.0-R5.7.md`.


## R5.7.15 Target Canvas Optical Evidence Closure
- Preserve Shared Geometry V1.5 and R5.7.14 Data/CASE Integrity Core unchanged.
- Add target-level optical truth classification: exact / bounded / direct conflict / multi-source disagreement / unknown / not-applicable.
- Explicit `CF_CLOUD_CONDENSATE_ZERO` remains unresolved evidence conflict; it is not COT=0 and is never replaced by CF/RH/geometry inference.
- Formation output now carries target optical truth provenance/counts without changing Formation formulas, thresholds, or weights.
- `v1_target_canvas_optical_summary.csv` now reports exact/bounded/conflict/unknown counts and closure state.


## R5.7.16 Target Cloud Optical Response / Tier-1 Closure

R5.7.16 continues directly from the user-selected R5.7.15 Target Canvas Optical Evidence Closure baseline. It does not alter Formation thresholds, Viewing, Shared Geometry, or UI decision logic.

- Exact target COT retains deterministic Tier-1 six-band response.
- Bounded target COT now produces six-band radiance lower/upper bounds plus Brightness/Redness bounds, but is not promoted to an exact Formation response.
- Direct evidence conflicts and unknown optics remain unresolved; no CF/RH/geometry-to-COT inference is introduced.
- Cloud phase and effective-radius availability are carried as Tier-2 readiness provenance only; R5.7.16 does not invent wavelength-dependent scattering multipliers without a calibrated LUT/solver.
- NO_CANVAS cases preserve fixed target-optics schemas and zero-valued Formation provenance counters.
- Full regression: 329 passed / 0 failed.
