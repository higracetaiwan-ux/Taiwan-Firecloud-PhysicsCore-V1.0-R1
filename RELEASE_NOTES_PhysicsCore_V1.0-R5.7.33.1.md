# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.33.1

## Scope
Integrity-only hotfix. No science weights, Formation, Viewing, Photography, route resolution, 13-angle timeline, or six-band physics changed.

## Field trigger
R5.7.33 sunset CASE triggered a real CAMS 12h-cycle timeout for both `SPECTRAL_COLUMN_AOD` and `NATIVE_AEROSOL_532NM_PRESSURE_LEVEL` at -5.5/-6 deg. R5.7.28 correctly supplied real bounded spectral AOD fallback from the adjacent 09Z native column product, while native 3-D aerosol remained Missing.

## Bug
`TWILIGHT_GLOW_OBSERVER_AEROSOL_LONG_RANGE_COVERAGE` used spectral AOD readiness as a proxy for native 3-D `aerext532` readiness. This produced a false hard FAIL (`396/468`) even though all native-available targets were resolved and the remaining 72 targets were correctly Missing after provider timeout.

## Fix
Readiness is now evaluated per `time + solar_altitude_deg` from native 3-D provenance (`cams_native_aerosol_source`) and native pressure-level extinction (`cams_aerext532_m1_*`). Spectral AOD fallback cannot promote native 3-D readiness.

Expected field replay: `resolved=396/396;native_unavailable=72/468` => PASS.
