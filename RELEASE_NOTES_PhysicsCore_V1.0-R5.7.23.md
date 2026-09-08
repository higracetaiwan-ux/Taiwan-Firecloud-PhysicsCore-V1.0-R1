# Taiwan Firecloud PhysicsCore V1.0-R5.7.23 發行說明

## 版本主旨

**Genuine Liquid-Cloud Full Directional Calibration Pipeline / Domain Contract**

本版以 R5.7.22.1 ACCEPTED BASELINE 為唯一來源，沒有更改 Route Invariance、Formation / Viewing / Glow、Earth Shadow、六波段或 Target Optical Truth 的既有科學契約。

## 新增功能

1. 新增 `firecloud/tier2_liquid_directional_calibration_pipeline.py`。
2. 從 REAL Tier-2-ready liquid targets 建立第一版 calibration domain，不製造 synthetic target。
3. Production axes 維持：`COT × r_eff × θ₀ × θᵥ × Δφ × wavelength`。
4. 新增 libRadtran / uvspec MYSTIC spherical 外部 job recipe 與 template。
5. 新增 target-local `θᵥ → uvspec umu` 幾何 adapter。
6. 新增 external RT result schema、完整 job-set QC、Monte-Carlo convergence gate、solver provenance gate。
7. 新增 genuine external results → calibrated runtime package builder。
8. 新增兩個 CLI：校準 job bundle generator、external-result production package builder。
9. 新增 R5.7.23 專屬 regression tests。

## 安全邊界

本建置環境未偵測到 `uvspec`，因此本版**沒有產生或安裝 genuine calibrated production LUT**。

狀態必須保持：

`NOT_YET_GENERATED_EXTERNAL_RT_REQUIRED`

不得以 synthetic / regression-only response 取代真正的 libRadtran/MYSTIC 或其他經驗證的 full-hemisphere RT 結果。

## 相容性

- R5.7.22.1 Reference Route / 1180 km provider domain 保持不變。
- 13-angle `0° → −6° / 0.5°` 保持不變。
- 六波段 550 / 575 / 600 / 650 / 700 / 750 nm 保持不變。
- Legacy scattering-angle-only LUT 仍不得作 production Tier-2 LUT。
- `cloud_thickness_km` 仍不是 production scattering LUT interpolation axis。
