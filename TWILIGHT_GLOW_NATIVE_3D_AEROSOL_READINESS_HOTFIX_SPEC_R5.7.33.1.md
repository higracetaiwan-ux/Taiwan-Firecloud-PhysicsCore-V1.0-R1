# R5.7.33.1 Native 3D Aerosol Readiness Integrity Hotfix

## Frozen separation
`Spectral column AOD` and `native 3-D aerosol extinction` are different evidence chains. A real bounded fallback may satisfy the former under R5.7.28 but can never satisfy the latter.

## Guard contract
For 60/80/100 km Glow observer targets:
1. Build readiness per `time + solar_altitude_deg`.
2. Native-ready requires >=95% route rows with non-empty `cams_native_aerosol_source` and numeric native `cams_aerext532_m1_*`.
3. Require all six aerosol tau values only for targets whose time-angle is native-ready.
4. Native-unavailable targets remain Missing and are reported separately; they do not become clear/zero and do not cause a false coverage FAIL.
5. If native-ready targets exist but any lacks six-band aerosol tau, FAIL.
6. If no native-ready targets exist, WARN rather than fabricate evidence.
