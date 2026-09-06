# Taiwan Firecloud PhysicsCore V1.0-R5.6

## Viewing + Photography Decision Layer

R5.6 adds the first formal Cloud→Observer branch while preserving the frozen physical separation:

- Formation = Sun→CloudBase
- Viewing = Cloud→Observer
- Photography Decision = outer operational interpretation only

### New CASE evidence

- `v1_viewing_path_geometry.csv`
- `v1_viewing_summary.csv`
- `v1_photography_decision.csv`

### Tier-1 Viewing contract

For every target Canvas cloud, R5.6 traces three Cloud→Observer sight-lines (base/mid/top) through nearer cloud layers on the same direction transect, with curved-Earth LOS height correction. Intervening cloud fraction is retained only as a geometric occupancy proxy after an intersection is established.

This is **not** full viewing-path spectral radiative transfer. The output explicitly reports `VIEW_SPECTRAL_RT_NOT_YET_RESOLVED`.

### Viewing states

- `VIEW_GEOMETRICALLY_CLEAR`
- `VIEW_PARTIAL_OBSTRUCTION`
- `VIEW_SEVERE_OBSTRUCTION`
- `VIEW_GEOMETRY_UNKNOWN`

### Photography outcomes

- `PHOTOGRAPHABLE_FIRECLOUD`
- `PARTIALLY_PHOTOGRAPHABLE_IF_FORMATION_OCCURS`
- `FORMED_OR_POSSIBLY_FORMED_BUT_NOT_PHOTOGRAPHABLE_FROM_OBSERVER`
- `VISIBLE_CLOUD_BUT_NO_FIRECLOUD_FORMATION`
- `VIEW_OPEN_BUT_FORMATION_UNRESOLVED`
- `PHOTOGRAPHY_OUTCOME_UNKNOWN`

### Frozen safeguards

- Viewing never changes `F_sun`.
- Viewing never changes Sun→CloudBase spectral RT.
- Viewing never changes Formation state.
- Photography Decision is not a Physics Score.
- Cloud fraction is not COT and is not converted to viewing optical depth.
- Missing viewing spectral RT remains Missing.

The 2026-09-06 sunset case is retained as the first calibration pattern for a physically illuminated/possibly illuminated target cloud that can still be partially or severely obscured from the observer.
