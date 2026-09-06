# Implementation Status — PhysicsCore V1.0-R5.7

## READY
- Finite solar disk / Penumbra geometry
- Six-band Sun→CloudBase gas/aerosol/cloud path framework
- Forecast-native GFS cloud microphysics
- DWD ICON secondary native cloud optics with unstructured-grid + vertical reconstruction
- Canvas Optical Suitability
- Projected-volume / angular-footprint Viewing geometry
- Cloud→Observer six-band gas/aerosol/cloud diagnostic RT
- Forecast-native 3-D hydrometeor precipitation path for Formation and Viewing when RWMR/SNMR/GRLE are available
- Formation / Viewing / Photography Decision separation

## CONDITIONAL / DATA-DEPENDENT
- Full Six-Band Formation closure: closes only when every required component has real optical evidence.
- Viewing Full Six-Band RT: closes only when gas, aerosol, cloud and precipitation viewing components are resolved.
- 40–100 km target COT: remains Missing if neither primary nor secondary native optical evidence overlaps the target cloud.

## NOT CLAIMED
- Surface precipitation rate → tau conversion
- RH / cloud fraction / geometry → COT conversion
- Satellite observation as forecast input
- Calibrated photographic threshold from Viewing spectral transmission
- Single Physics Score
