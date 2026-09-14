# Test Report — V1.0-R5.7.41.3.4.10.10

## Scope

Ice Cloud Spectral Optics Shared Module Phase 1 + WINDY shared export。Frozen science 不改。

## 新增/更新測試

- 版本與固定六波段 contract
- `Qext × A / (rho_ice × V)` mass-extinction 單位轉換
- TAMU/Yang-Bi `isca.dat` six-band normalizer
- exact zero / Missing / incomplete vertical support 語意
- positive IWP + no calibrated LUT fail-close
- `tau_ice = IWP × k_ext` diagnostic formula
- WINDY compact CSV/JSON contract
- Ice Optics Analysis Integrity guards
- CASE required-artifact contract

## Regression

- New Ice Optics targeted tests：8/8 PASS
- Full working-tree regression：**741/741 PASS**
- Warning：1 existing pandas FutureWarning（既有測試，非 `.10.10` 新增）

## Offline actual-CASE proxy

基礎：`.10.9.9` TWS089 2026-09-15 sunrise。

- runtime：2691 rows
- summary：78 rows
- WINDY summary：78 rows
- positive IWP：1713 rows
- positive IWP 但 calibrated inputs 不完整時，spectral tau fabricated rows：0

## Frozen science source audit

相對 `.10.9.9`：Formation、Viewing、Viewing Spectral、Twilight Glow、Gas RT、Cloud Optics、Config、Red-Light、Photography、Native Cloud、Formation Gates/Prerequisites、Spectral RT/Color、Illumination、Optical Path 共 **16/16 核心 science files byte-identical**。詳細 hash audit：`FROZEN_SCIENCE_SOURCE_AUDIT_R5.7.41.3.4.10.10.csv`。

## Release Gate

- Working-tree regression：PASS
- Frozen science audit：**PASS（16/16 byte-identical）**
- FULL-CLEAN fresh-extract regression：**741/741 PASS**（1 existing pandas FutureWarning）
- Field CASE：PENDING
