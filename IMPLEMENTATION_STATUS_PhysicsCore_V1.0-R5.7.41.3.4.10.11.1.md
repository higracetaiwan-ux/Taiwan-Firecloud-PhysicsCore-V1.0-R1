# Implementation Status — V1.0-R5.7.41.3.4.10.11.1

- Version: `1.0.0-R5.7.41.3.4.10.11.1`
- Science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`
- Previous field baseline: `.10.10.2 = FIELD PASS`
- Milestone: TAMU V2 Source Contract Correction + Dmax-First Ice LUT
- Physics promotion: **NO**
- WINDY runtime dependency on PhysicsCore: **NONE**
- Portable contract: `FIRECLOUD_ICE_OPTICS_PORTABLE_V1_1`

## Completed

- `HC -> hollow_column` source resolver
- source-row wavelength-dependent geometry acceptance with explicit diagnostic provenance
- Dmax-first authoritative LUT QA
- Dmax-first portable Python / JS / TS evaluator
- Dmax exact/interpolation/no-extrapolation contract
- fail-close no-Dmax semantics
- V1.1 standalone SDK
- real HBR/SBR sample verification
- full regression
- frozen science audit

## Pending user full-source retest

本環境沒有使用者本機 27.4 GB archive 與完整 extracted source tree，因此 `.10.11.1` 最終 authoritative 27/27 source gate 必須在使用者本機重跑。

目標：27/27 source、162/162 spectral、30618 LUT rows、5103 six-band Dmax groups、`release_ready=true`。
