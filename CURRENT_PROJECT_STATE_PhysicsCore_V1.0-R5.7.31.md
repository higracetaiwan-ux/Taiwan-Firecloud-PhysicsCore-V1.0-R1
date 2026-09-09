# Taiwan Firecloud PhysicsCore — Current Project State V1.0-R5.7.31

狀態日期：2026-09-09（台灣時間）

## Current Production Candidate

- 候選版本：**V1.0-R5.7.31**
- 主題：**Twilight Glow Full Six-Band Extinction Phase 1**
- 狀態：**CODE COMPLETE / FIELD VALIDATION OPEN**

## 已 Field Closed 的前置契約

- R5.7.27 Formation-first Photography Decision
- R5.7.27.1 Photography Integrity handoff
- R5.7.29.1 Viewing precipitation spool handoff
- R5.7.30.1 Integrity regression restore

## R5.7.31 新增

- `Sun→Scatter` 六波段 component extinction
- `Scatter→Observer` 六波段 component extinction
- O3 與非 O3 gas 分離
- 三張 versioned Glow CASE evidence tables
- R5.7.31-only target coverage / numeric closure Integrity

## 凍結規則

- 13 angles：0° 到 −6°，每 0.5°
- 六波段：550/575/600/650/700/750 nm
- Formation = Sun→CloudBase
- Viewing = Cloud→Observer
- Glow = independent Sun→Atmosphere→Observer branch
- Missing ≠ Clear ≠ Zero ≠ N/A
- Forecast / Observation / Nowcast 永久分離
- Route Invariance 不變
- Glow 不得修改 Photography Formation-first hard gate

## 尚未完成

- R5.7.31 真實部署 CASE field validation
- R5.7.28 CAMS adjacent-time fallback 尚待真實 provider failure 觸發
- Aerosol scattering SSA / phase function
- Multiple scattering
- Absolute sky-radiance calibration
- Genuine calibrated Tier2 cloud directional LUT
