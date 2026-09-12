# R5.7.41.3.4.1 — Twilight Glow Explicit-Missing Integrity Hotfix

- Historical replay may legitimately have an empty/unavailable cloud-volume table.
- `twilight_glow.py` already emits `GLOW_OBSERVER_CLOUD_EVIDENCE_MISSING`.
- Integrity now recognizes this explicit Missing provenance as preserved Missing, provided cloud tau stays NaN and six-band evidence stays MISSING.
- Missing is not promoted to clear or zero optical depth.
- No Production COT, Shadow COT, Formation, Viewing, Glow physics, or threshold changes.
