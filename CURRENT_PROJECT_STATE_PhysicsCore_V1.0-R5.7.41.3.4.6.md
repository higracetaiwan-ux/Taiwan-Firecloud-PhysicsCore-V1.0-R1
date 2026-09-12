# Taiwan Firecloud PhysicsCore — Current Project State

Current release: **V1.0-R5.7.41.3.4.6 — Runtime / I-O Hardening**.

Science baseline remains frozen:

`R5.7.41.2_SHADOW_COT_AB_FROZEN`

## R5.7.41.3.4.5 field result

TWS106 2026-09-12 Sunset A/B proved Viewing→Glow provenance handoff is science-equivalent and effective:

- 1092/1092 handoff hits;
- cloud provenance fallback 0;
- Glow 119.20 s → 91.14 s (-23.5%);
- core science CSV exact equality;
- total runtime was contaminated by DWD external I/O variance (80.94 s → 215.35 s).

The same CASE also exposed an audit defect: 176 true DWD network downloads were reported as 0 by `api_efficiency_audit.csv`.

## R5.7.41.3.4.6 scope

1. DWD persistent raw cache with exact identity + SHA256/QC guard;
2. DWD API efficiency audit correction;
3. CASE buffered ZIP streaming + detailed export telemetry;
4. aggregation hotspot profiling only.

## Safety boundary

No changes to:

- Production / Shadow COT;
- Shadow candidate eligibility;
- Earth Shadow / finite solar disk / refraction;
- Formation / Viewing / Twilight Glow;
- six-band spectroscopy;
- Missing / direct-conflict semantics;
- Production/COT/Formation promotion flags.

## Verification

- focused Runtime/I-O tests: 12/12 PASS;
- working-tree full regression: 628/628 PASS;
- one existing pandas FutureWarning only;
- trial fresh-extract full regression: 628/628 PASS;
- final-candidate fresh-extract full regression: 628/628 PASS;
- final FULL-CLEAN exact-archive fresh-extract full regression: 628/628 PASS;
- Release Gate: **CLOSED**.

## Next

After a real R5.7.41.3.4.6 CASE provides the new aggregation profile rows, R5.7.41.3.4.7 should optimize only the largest measured aggregation hotspot. Shadow CASE collection continues opportunistically with weather and does not block engineering development.
