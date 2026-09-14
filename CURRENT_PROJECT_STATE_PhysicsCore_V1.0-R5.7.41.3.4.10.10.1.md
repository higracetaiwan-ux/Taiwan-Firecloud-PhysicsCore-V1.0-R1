# Taiwan Firecloud PhysicsCore — Current Project State

> 版本：**V1.0-R5.7.41.3.4.10.10.1**  
> Internal：`1.0.0-R5.7.41.3.4.10.10.1`  
> 名稱：**Ice Optics Portable WINDY Runtime Decoupling**  
> Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`  
> Release state：**REGRESSION PASS / FIELD RETEST CANDIDATE**

## 現行科學主線

`.10.10` 已建立 Ice Cloud Spectral Optics Phase 1：六波段、calibrated LUT contract、IWP×k_ext、strict Missing semantics、diagnostic-only role separation。

`.10.10.1` 正式凍結部署架構：

**PhysicsCore builds/certifies → portable Ice LUT package → WINDY imports → WINDY standalone runtime**。

WINDY 不再以「每次由 PhysicsCore 分析後輸出 runtime result」作為長期架構。

## Portable package

Contract：`FIRECLOUD_ICE_OPTICS_PORTABLE_V1`。

Package 有 calibrated LUT 時包含：LUT CSV/JSON、contract、manifest、SHA256、TypeScript/ESM reference evaluator、cross-language validation vectors、Node validator、source provenance。

WINDY runtime dependencies：PhysicsCore=NONE；Python=NONE；Streamlit=NONE。

## 現有 WINDY Summary

`.10.10` 的 `v1_windy_ice_optics_summary.csv` / JSON 保留作 Field validation/debugging，但不是 WINDY standalone runtime dependency。

## LUT readiness

目前 release **仍未附帶 authoritative calibrated coefficient table**。這是刻意 fail-close：source family 已選定 Yang/Bi V2，但未完成 authoritative LUT build/certification前，不提供假係數。

`ice_optics_portable_sdk_v1/` 可先供 WINDY 開發介面與 evaluator；真正 consumer package 必須用 calibrated LUT 經 `tools/build_ice_optics_portable_package.py` 產生。

## Integrity

除 `.10.10` 既有五個 Ice gates 外，新增：

`ICE_OPTICS_PORTABLE_WINDY_RUNTIME_DECOUPLING`

CASE 新增：

`ice_optics_portable_consumer_contract.json`

## Regression

- targeted Ice/Portable tests：14/14 PASS + standalone TS compile gate PASS
- full working-tree regression：748/748 PASS
- final FULL-CLEAN fresh-extract regression：748/748 PASS
- existing warning：1 個 pandas FutureWarning（既有）
- Frozen science source audit vs `.10.10`：16/16 byte-identical

## 下一步

1. 正式取得/整理 authoritative Yang/Bi V2 source files，生成六波段 calibrated LUT。
2. 做 LUT science QA：habit/roughness/size coverage、Qext/A/V unit audit、six-band interpolation provenance。
3. 以 calibrated LUT 建出第一個 `Firecloud-Ice-Optics-Portable` 正式 package，執行 Python↔JS/TS parity。
4. WINDY 匯入 package，先只做 standalone diagnostic；不依賴 PhysicsCore runtime。
5. Phase 2 再處理 habit mixture / PSD / effective-size provenance / phase function。
6. Phase 3 需另立 science release gate，才可能進 Formation/Canvas/Viewing production physics。
