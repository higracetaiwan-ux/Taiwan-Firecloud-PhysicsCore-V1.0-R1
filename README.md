# Taiwan Firecloud PhysicsCore V1.0-R5.6

R5.6 adds an independent Cloud→Observer Viewing branch and an outer Photography Decision Layer on top of the R5.5.2 optical-closure baseline. Formation remains Sun→CloudBase physics; Viewing never rewrites whether the cloud was illuminated.

See `RELEASE_NOTES_PhysicsCore_V1.0-R5.6.md` and `IMPLEMENTATION_STATUS_PhysicsCore_V1.0-R5.6.md`.

---


R5.5.2 closes two runtime optical-evidence gaps on top of R5.5.1 while preserving the frozen PhysicsCore separation:

- **Penumbra Geometry** computes only finite-solar-disk / Earth-shadow geometry (`F_sun`).
- **Sun→CloudBase Spectral RT** computes path extinction/transmission.
- **Target Cloud Optical Response / Canvas Optical Suitability** remains an independent target-cloud layer.

## R5.5.2 additions

1. **DWD ICON Global unstructured-grid decoder closure**
   - Uses DWD's official `ICON_GLOBAL2WORLD_025_EASY` CDO nearest-neighbour weight bundle.
   - Maps each route point to the native ICON source-cell address before downloading QC/QI fields.
   - Reads native GRIB `values` by source address; it no longer requests nonexistent per-cell `latitudes/longitudes` from ICON Global GRIB.
   - Grid-mapping failure aborts the ICON branch before mass QC/QI downloads.
   - Audit states distinguish grid-map failure, field decode failure, unresolved microphysics, zero condensate and positive condensate.

2. **Sun→CloudBase upstream cloud optical closure**
   - Forecast-native secondary COT (IFS / DWD ICON) may resolve upstream cloud-path opacity when the primary CloudScene has geometry but lacks primary COT.
   - The bridge is path-only: it does not rewrite CloudScene geometry and does not promote Canvas Optical Suitability.
   - Horizontal support still requires adjacent forecast-native optical evidence on both sides; route sampling distance is never treated as cloud width.
   - Missing/partial evidence remains Missing; no RH/CF/geometry → COT conversion is introduced.

3. **Dependencies**
   - Adds `scipy>=1.10` to read DWD CDO NetCDF nearest-neighbour weight addresses.

See `RELEASE_NOTES_PhysicsCore_V1.0-R5.5.2.md`.
