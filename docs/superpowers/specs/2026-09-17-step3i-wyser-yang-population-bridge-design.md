# Step 3I — Wyser ↔ Yang/Bi Population Bridge Design

## Goal
Qualify an explicit diagnostic bridge between the Wyser mixed PSD/mass normalization and the Yang/Bi V2 `single_column` optical kernel on the already-qualified common maximum-dimension coordinate, without asserting shape/mass equivalence or enabling production ice optics.

## Frozen constraints
- Science baseline remains `R5.7.41.2_SHADOW_COT_AB_FROZEN`.
- Formation, Viewing, Twilight Glow, six-band transport, Canvas/Corridor/REZ, Earth Shadow, Production/Shadow COT and Missing≠Clear≠Zero are unchanged.
- Step 3H coordinate result remains: `Wyser L_um == Yang/Bi maximum_dimension_um` as size coordinate only.
- No hidden habit or roughness default may be promoted to runtime.
- `INDEPENDENT_EQ6_EXTERNAL_NUMERIC_CORROBORATION_PASS` remains false unless an independent exact-numeric source is found.
- No production `tau_ice`, Dmax synthesis, Formation promotion, or WINDY validated mapping is enabled in Step 3I.

## Architecture
Create a new Step 3I module rather than rewriting Step 3H history. The module explicitly keeps two particle-mass semantics separate:
1. **Wyser population mass**: Eq.(6), used only for PSD/IWC normalization.
2. **Yang optical-kernel mass**: `rho_ice * V_yang`, used only to invert the portable LUT mass-extinction coefficient into single-particle extinction cross section `C_ext = k_ext * m_yang`.

The Yang kernel geometry uses the Step 3H source-reproduced V2 `single_column` law. At the same Dmax, Wyser Eq.(5) geometry and Yang geometry are compared numerically for width, mean projected area, volume, and mass. These comparisons remain non-equivalence diagnostics; no ratio is used to silently remap one geometry into the other.

## Step 3I gates
May pass:
- `YANG_BI_SINGLE_COLUMN_KERNEL_CEXT_RECONSTRUCTION_PASS`: all bundled Rough000 single-column rows in the Wyser 10–1000 µm domain have finite positive Yang mass, projected area, reconstructed Cext and reconstructed Qext with complete six-band coverage.
- `WYSER_YANG_DUAL_MASS_SEMANTICS_SEPARATED_PASS`: contract explicitly separates population mass from optical-kernel mass.
- `WYSER_YANG_HYBRID_POPULATION_BRIDGE_NUMERIC_EXECUTABLE`: diagnostic number-density × Yang-Cext bridge has all required numeric ingredients on the shared Dmax axis.

Must remain false in Step 3I:
- direct shape compatibility
- projected-area equivalence
- volume/mass equivalence
- independent Eq.(6) corroboration
- scientific mass closure promotion
- habit bridge
- roughness bridge
- bulk Yang/Bi PSD integration eligibility
- GFSv16 Dmax mapping eligibility
- production ice optics / physics promotion

## Evidence
Step 3I evidence will quantify the full bundled `single_column/Rough000` overlap within 10–1000 µm, including size count, six-band row count, reconstructed Qext range, and Wyser↔Yang area/volume/mass ratio ranges. Evidence must be portable and deterministic after fresh extraction.

## CASE handoff
Add independent Step 3I evidence CSV, gate CSV, and contract JSON to model outputs, Analysis Integrity, CASE required members, archive manifest/content checks, and app export. Step 3H artifacts remain unchanged and continue to be archived.

## Success criteria
- TDD RED→GREEN for core diagnostics and CASE handoff.
- Full regression green.
- Evidence/gate/contract deterministic regeneration exact after fresh extract.
- FULL-CLEAN ZIP contains no cache/bytecode artifacts.
- Release status remains `QA PASS / FIELD VALIDATION PENDING`; FIELD PASS requires a real CASE.
