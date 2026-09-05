# Taiwan Firecloud PhysicsCore V1.0-R4.5.2

## Geometry / Optics Evidence Decoupling

R4.5.2 fixes the evidence-coupling defect exposed by the R4.5.1 real CASE: once native CLWMR/ICMR became available, zero condensate was incorrectly allowed to erase independent cloud-fraction geometry evidence, which removed 0–100 km Canvas candidates.

### Changes
- Cloud occupancy is now classified from independent geometry evidence first.
  - Native cloud fraction > provider clear threshold preserves `PARTIAL_OCCUPANCY` or `CLOUD_OCCUPIED`.
  - Positive native condensate can independently establish occupancy when cloud fraction is low/missing.
  - Zero condensate can no longer erase non-zero cloud-fraction occupancy evidence.
- Optical evidence remains independent.
  - `CF_CLOUD_CONDENSATE_ZERO` preserves geometry but leaves COT unresolved (`GEOMETRY_ONLY`, `cot=Missing`).
  - `CONDENSATE_CLOUD_CF_LOW` is treated as an evidence conflict and does not become trusted COT.
  - Consistent cloud fraction + positive condensate continues to produce native-condensate COT.
- `CloudLayer` now exports `evidence_consistency` for CASE audit.
- No RH/cloud-fraction/base/top proxy is used to fabricate COT.
- Canvas candidate generation continues to use CloudScene geometry only; it does not require optical evidence.

### Evidence consistency states
- `CONSISTENT_CLOUD`
- `CONSISTENT_CLEAR`
- `CF_CLOUD_CONDENSATE_ZERO`
- `CONDENSATE_CLOUD_CF_LOW`
- `OPTICS_MISSING`
- `OPTICS_AND_GEOMETRY_MISSING`
- `CONDENSATE_ONLY_POSITIVE`
- `CONDENSATE_ONLY_ZERO`

### Physics boundary preserved
`Geometry evidence != Optical evidence`. A disagreement is recorded, not silently reconciled into a score or invented optical depth.
