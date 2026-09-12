# Twilight Glow Runtime Cache Hardening Spec — R5.7.41.3.4.4

## Scope

Engineering-only optimization for observer-cloud conflict provenance inside the independent Twilight Glow branch.

## Allowed cache identities

Cache may reuse only evidence that is invariant for the exact same:

- event `time`;
- `solar_altitude_deg`;
- `direction_offset_deg`;
- cloud-layer identity / source row;
- immutable cloud/target-optics evidence tables within one analysis run.

## Cached objects

- grouped cloud transect;
- exact COT evidence lookup;
- target optical truth provenance lookup;
- projected horizontal support interval for a cloud layer inside one exact transect.

## Forbidden

Cache must not:

- cross a different time, solar angle or direction;
- synthesize missing COT;
- convert conflict to clear/zero;
- reuse Sun→CloudBase Formation state as Cloud→Observer evidence;
- alter DirectSolarFraction, Earth Shadow, six-band extinction or scattering formulas;
- change any Production/Shadow decision.

## Telemetry

`TWILIGHT_GLOW_INDEPENDENT_BRANCH` reports cache contract/status and counts. Existing inclusive aggregation timer remains for backward comparison; a new engineering-only excluding-Glow timer is emitted separately.
