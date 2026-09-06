# Taiwan Firecloud PhysicsCore V1.0-R5.6.1

R5.6.1 is the corrected Viewing / Photography release on top of the R5.5.2 optical-closure baseline.

Core separation remains frozen:

- **Formation:** Sun → CloudBase illumination physics.
- **Viewing:** Cloud → Observer visibility/obstruction physics.
- **Photography Decision:** outer operational interpretation of whether the event is actually photographable from the selected observer.
- **Penumbra Geometry** and **Spectral RT** remain independent physical layers.

R5.6.1 replaces the R5.6 point-node Viewing test with projected adjacent-node cloud-volume support, excludes foreground low clouds from the firecloud-target summary while retaining them as blockers, and closes the DWD ICON vertical-geometry gap using native P/T with a route-specific forecast surface anchor instead of unavailable per-level FI files.

See `RELEASE_NOTES_PhysicsCore_V1.0-R5.6.1.md` and `IMPLEMENTATION_STATUS_PhysicsCore_V1.0-R5.6.1.md`.
