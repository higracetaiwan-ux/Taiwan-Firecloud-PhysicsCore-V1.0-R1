# Taiwan Firecloud PhysicsCore — Release Notes

版本：`1.0.0-R5.7.41.3.4.10.30.9`
名稱：**Step 3Q.9 — v2.5 Mirror Import-Time / Historical-CVS-Time Separation + Official Runtime Solar Context Qualification**

## 本版變更
- 正式分離第三方 GitHub 鏡像的 **2020 import time** 與鏡像內 AER CVS metadata 的 **2004 historical source time**。
- 固定規則：不得把 GitHub import timestamp 當成原始 AER source date，也不得把它當成 original AER tarball authenticity 證據。
- 納入 AER 官方 RRTMG_SW 描述：RRTM_SW runtime 使用 Kurucz solar source，固定 solar constant 1368.22 W/m²；RRTMG_SW absorption data 與 RRTM_SW_v2.5 一致。
- 固定規則：上述 runtime solar context 不等於 Fu cloud-table pre-averaging high-resolution spectral weights。
- 原 `.10.30.8` v2.5 external distribution lineage、CVS provenance、low/high-resolution Kurucz distinction 全部保留。
- Formation / Viewing / Twilight Glow、六波段、Canvas / Corridor / REZ、Earth Shadow、Production/Shadow COT、Missing≠Clear≠Zero 全部不變。

## 正式 qualification state
`PASS_FAIL_CLOSED_V25_MIRROR_TIME_AND_RUNTIME_SOLAR_CONTEXT_QUALIFIED_PREAVERAGING_GENERATOR_UNRECOVERED`

## 仍然 fail-close
- Q. Fu high-resolution pre-averaging tables：未恢復
- historical band-averaging generator：未恢復
- exact band-24 / band-25 reproduction：未完成
- exact solar grid / discrete weights：未恢復
- `EXACT_FU96_BAND_WEIGHTING_AVAILABLE=False`
- `TAU_ICE_PRODUCTION_ALLOWED=False`
- `PRODUCTION_ICE_OPTICS_READY=False`
- Step 3R：blocked

## Release artifact SHA256
- evidence: `6d8539c8199beaafd23e6c0ecd32af69707178e129dc945d190359befe4c4069`
- gate: `8a258604e710b2ddae2fe975201ff33c17a410cc9ea9662726c719bfb34dc086`
- contract: `a0d35a7bd41c4473280cda69482c00de6c9f96160ab1808c8390e48d1a2c8f9f`
