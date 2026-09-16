# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.16

## Ice Optics Phase 2 Step 3C — GFS v16 Effective-Radius ↔ Yang/Bi Dmax Bridge Feasibility Audit

本版沒有加入新的 Ice τ 計算，也沒有啟用 Dmax mapping。主要變更是把 `GFDL/Wyser rei` 與 `Yang/Bi Dmax` 的語義差異正式寫入可稽核 evidence/gate。

### New
- `firecloud/ice_microphysics_gfsv16_rei_dmax_bridge.py`
- Step 3C evidence / gate / contract
- 3 個 Analysis Integrity hard gates
- 3 個 CASE archive required members
- 3 個 CASE archive serialized-content gates
- Step 3C performance diagnostic stage

### Scientific decision
- direct `rei → Dmax`: rejected
- `Dmax = 2 × rei`: rejected
- generalized effective diameter as Dmax: rejected
- bulk PSD integration over authoritative Yang/Bi single-particle Dmax LUT: identified, not qualified

### Provenance caution
Public GFDL parameter comments and the actual v1/2019 `reiflag=2` source branch contain a label mismatch. The mismatch is preserved as evidence and blocks production mapping until authoritative operational provenance is stronger.

### Frozen
`R5.7.41.2_SHADOW_COT_AB_FROZEN` unchanged. Formation / Viewing / Twilight Glow / six bands / Canvas / Corridor / REZ / Earth Shadow / Production-Shadow COT / Missing≠Clear≠Zero remain unchanged.

### Status
Implementation/regression PASS. FIELD validation pending. Latest FIELD PASS remains `.10.15.1`.
