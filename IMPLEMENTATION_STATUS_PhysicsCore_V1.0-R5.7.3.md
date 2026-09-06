# PhysicsCore V1.0-R5.7.3 Implementation Status

R5.7.3 is a performance-stability hotfix on top of R5.7.2. All R5.7 physics remain unchanged. The 0.93 aggregation stage now caches viewing transects, projected supports, CF neighbours, route groups, gas RT contexts, exact-COT maps, and cloud support geometry to eliminate repeated full-DataFrame scans.

Resolved blocker:
- Viewing route snapshot export no longer duplicates the existing `time` column.

Regression status:
- 288 passed / 0 failed.
