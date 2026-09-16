# Release Notes — PhysicsCore V1.0-R5.7.41.3.4.10.13

## 名稱

**Ice Optics Phase 2 Step 2 — Authoritative Size/PSD Source Capability Registry + Eligibility Gate**

## 本版新增

- 新增 `firecloud/ice_microphysics_source_registry.py`。
- 新增 6 類 authoritative/reference source capability survey：NOAA GFS、DWD ICON Global、ECMWF IFS Open Data、ECMWF IFS effective-size reference、NASA GEOS-FP、NOAA RAP reference。
- 新增 runtime/CASE artifacts：
  - `ice_microphysics_source_capability_registry.csv`
  - `ice_microphysics_source_eligibility_gate.csv`
  - `ice_microphysics_source_registry_contract.json`
- 新增 Analysis Integrity checks：
  - `ICE_MICROPHYSICS_SOURCE_REGISTRY_EVIDENCE_PRESENT`
  - `ICE_MICROPHYSICS_SOURCE_REGISTRY_CONTRACT_FREEZE`
  - `ICE_MICROPHYSICS_SOURCE_SELECTION_FAIL_CLOSED`
- CASE Archive Integrity 將上述三項 evidence 納入 required members。

## 現行結論

截至 2026-09-16，調查到的全球、台灣可用候選來源仍沒有 direct Yang/Bi-compatible Dmax 或 production-ready PSD，因此 source gate 維持：

`NO_AUTHORITATIVE_TAIWAN_SIZE_OR_PSD_SOURCE`

## 未更動

- Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`
- Formation / Viewing / Twilight Glow
- 550/575/600/650/700/750 nm 六波段
- Canvas / Corridor / REZ / Earth Shadow
- Production / Shadow COT
- Missing ≠ Clear ≠ Zero
- Dmax-first Yang/Bi runtime contract
- WINDY portable decoupling

本版不新增任何 provider download，不建立 r_eff→Dmax、IWP→Dmax、mass+number→Dmax、habit、roughness 或 assumed PSD 規則。
