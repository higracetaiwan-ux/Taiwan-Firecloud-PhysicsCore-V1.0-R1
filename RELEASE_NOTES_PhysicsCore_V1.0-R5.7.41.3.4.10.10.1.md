# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.10.1

## Ice Optics Portable WINDY Runtime Decoupling

本版延續 `.10.10` Ice Cloud Spectral Optics Phase 1，但把「共用模組」正式改成 **共用科學 artifact，而不是共用 runtime service**。

### 新增

- `firecloud/ice_optics_portable.py`
- `tools/build_ice_optics_portable_package.py`
- `ice_optics_portable_sdk_v1/`
- Portable contract：`FIRECLOUD_ICE_OPTICS_PORTABLE_V1`
- dependency-free ES module evaluator
- standalone TypeScript evaluator
- portable manifest + SHA256 file inventory
- cross-language reference validation vectors
- Node standalone validation runner
- LUT/manifest JSON schemas
- CASE artifact：`ice_optics_portable_consumer_contract.json`
- Integrity：`ICE_OPTICS_PORTABLE_WINDY_RUNTIME_DECOUPLING`
- Streamlit：calibrated LUT READY 時可直接下載 WINDY standalone portable ZIP

### Deployment rule

PhysicsCore 是 Ice Engine/LUT 的 authoring/calibration/release authority；WINDY 發布時只攜帶 portable package，之後 local runtime lookup/interpolation，不呼叫 PhysicsCore。

Portable manifest 固定：

- `runtime_dependency_on_physicscore = NONE`
- `runtime_dependency_on_python = NONE`
- `runtime_dependency_on_streamlit = NONE`

### 不變

- Ice Optics 六波段：550/575/600/650/700/750 nm
- `tau_ice = IWP × k_ext`
- `T = exp(-tau)`
- Missing semantics
- `.10.10` diagnostic-only/no physics promotion gate
- Frozen Formation / Viewing / Twilight Glow / COT / Red-Light / Photography science

本版仍未附帶未校準 Ice LUT 係數；沒有 authoritative calibrated LUT 時，不產生可執行 consumer LUT package。
