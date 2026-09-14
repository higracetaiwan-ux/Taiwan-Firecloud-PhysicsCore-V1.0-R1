# WINDY Firecloud Observer — Ice Optics Standalone Integration Guide V1

## Runtime flow

`WINDY forecast/observation input → normalize IWP/reff/habit/roughness → local portable LUT lookup → tau/T/SSA/g diagnostics → WINDY UI`

WINDY 不呼叫 PhysicsCore。

## Import

正式 package 使用：

- `ice_optics_lut_v1.json`
- `windy/iceOpticsEvaluator.ts`（或 `.mjs`）
- `contract.json`
- `manifest.json`

WINDY build/release 前先執行 package 內：

`node validation/validatePackage.mjs`

## Fail-close states

應直接顯示/保存：

- `ICE_IWP_MISSING`
- `ICE_IWP_INCOMPLETE_NATIVE_VERTICAL_SUPPORT`
- `ICE_EFFECTIVE_RADIUS_MISSING`
- `ICE_HABIT_MISSING`
- `ICE_ROUGHNESS_MISSING`
- `ICE_HABIT_ROUGHNESS_NOT_IN_LUT`
- `ICE_REFF_OUTSIDE_LUT_DOMAIN`
- `ICE_SIX_BAND_OPTICS_READY`

不得把 Missing 顯示成 clear/zero。

## Integration phase

Phase 1：WINDY diagnostic only。即使 local evaluator能算 tau，也不得自行把它變成 Firecloud Formation hard blocker / Canvas production COT，直到 PhysicsCore Phase 3 science gate正式發布對應 role contract。
