# PhysicsCore V1.0-R4.8 implementation status

Implemented the operational path needed to actually generate the missing 550 nm spectroscopy rather than merely diagnose it. The shipped package intentionally does not redistribute raw HITRAN transition line lists. Users must import/download H2O and O2 535–765 nm line data once, then build and save the derived 432-state Runtime LUT.
