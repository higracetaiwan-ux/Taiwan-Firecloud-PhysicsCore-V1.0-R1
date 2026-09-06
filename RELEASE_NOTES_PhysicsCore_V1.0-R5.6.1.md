# Taiwan Firecloud PhysicsCore V1.0-R5.6.1

## Purpose
R5.6.1 corrects the runtime issues exposed by the 2026-09-06 sunset CASE without collapsing Formation, Viewing, Penumbra Geometry or Spectral RT.

## Changes
1. **Projected Cloud-Volume Viewing**
   - Replaces point-node-only obstruction checks with adjacent-node projected horizontal support.
   - Fixes near-observer 0–5 km clouds that can intersect the line of sight between sampled route nodes.
   - Missing blocker cloud fraction remains unknown; it is no longer synthesized as 50% occupancy.

2. **Photography-target summary scope**
   - Foreground low clouds (<2 km base) remain blockers.
   - They no longer count as firecloud targets in the overall Viewing/Photography summary.
   - Prevents low-cloud self-obstruction from falsely implying that high/mid firecloud canvases are obscured.

3. **DWD ICON vertical geometry closure**
   - Keeps the R5.5.2 official CDO source-address unstructured-grid decoder.
   - Stops depending on unavailable per-model-level FI files.
   - Reconstructs approximate model-level geometry from native P/T using route-specific forecast surface pressure and model-surface elevation as the anchor.
   - This is geometry only; QC/QI remain the only cloud condensate evidence used to derive secondary COT.

4. **Spectral RT dataframe performance cleanup**
   - Six-band diagnostic columns are created in one batch instead of repeatedly fragmenting the pandas DataFrame.
   - Equations and spectral values are unchanged.

## Frozen boundaries retained
- Formation ≠ Viewing ≠ Photography Decision.
- Penumbra Geometry ≠ Spectral RT.
- Missing ≠ Zero ≠ Clear.
- Cloud Fraction is not COT.
- Secondary provider geometry never fabricates cloud optics.

## Validation
- Full regression suite: **283 passed / 0 failed**.
- The 2026-09-06 R5.6 CASE re-evaluated with projected viewing detects the near-observer low-cloud volume in the 40 km high-cloud sight line, but only at the forecast cloud-fraction magnitude. It therefore reports a minor obstruction rather than falsely forcing a severe obstruction when the forecast itself under-represents the observed cloud cover.
