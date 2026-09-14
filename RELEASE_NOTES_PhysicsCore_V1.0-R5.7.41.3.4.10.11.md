# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.11

## 名稱

**Authoritative Ice LUT Source Intake + QA Build Gate**

## 新增

- 新增 `firecloud/ice_optics_authoritative.py`。
- 新增 Yang/Bi V2 authoritative source contract。
- 新增 9 habits × 3 roughness = 27 source-file inventory / QA。
- 新增六波段 source spectral-grid exact/interpolation audit。
- 新增 published archive MD5 gate。
- 新增 geometry consistency QA（V / projected area 不應隨 wavelength 漂移）。
- 新增 six-band LUT completeness / physical-range / duplicate-key / runtime-size-coordinate ambiguity gate。
- 新增 `tools/build_authoritative_ice_optics_lut.py`。
- 更新 `ice_optics_source_manifest_v1.json`，寫入 Zenodo record、archive/README checksum、habit/roughness/source counts。

## 明確未做

- 未內嵌 27.4 GB Yang/Bi V2 archive。
- 未內嵌假 `k_ext` / SSA / g。
- 未用 RH / Cloud Fraction / fixed r_eff / fixed habit 補造 Ice τ。
- 未將 Ice Optics 推進 Formation / Viewing / Twilight Glow production decision。

## Frozen science

`R5.7.41.2_SHADOW_COT_AB_FROZEN` 不變。

## 基線

`.10.10.2 = FIELD PASS`

`.10.11 = REGRESSION PASS / AUTHORITATIVE SOURCE BUILD READY / FIELD RETEST CANDIDATE`
