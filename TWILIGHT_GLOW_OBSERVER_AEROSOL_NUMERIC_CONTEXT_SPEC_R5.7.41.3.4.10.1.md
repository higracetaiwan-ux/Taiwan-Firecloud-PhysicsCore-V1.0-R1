# R5.7.41.3.4.10.1 — Twilight Glow Observer Aerosol Numeric Route Context Spec

## 問題
`.3.4.10` profiler 顯示 Twilight Glow 的 `OBSERVER_SPECTRAL_EXTINCTION` 為第一大 component。函式級 profile 指向 `_integrate_view_aerosol()`：1092 targets 對相同 aerosol route 重複 DataFrame 篩選與 pressure-level column reconstruction。

## Runtime-only solution
對每個 `(time, solar_altitude_deg, direction_offset_deg)` route 預先保存：
- ordered route distances；
- 每個 distance 的 native geopotential-height / CAMS ext532 numeric arrays；
- `spectral_aod_temporal_evidence_state` 結果；
- explicit 550/575/600/650/700/750 nm AOD。

Target integration 保留 legacy 語意：
1. 只使用 `distance <= target_distance` 的既有 route nodes。
2. 相同 curved-Earth observer LOS 高度。
3. 相同 native ext532 vertical interpolation。
4. 相同 Glow-only 0.05 km lowest native endpoint snap tolerance。
5. 相同 exact/one-sided temporal provenance判定。
6. 缺任一 explicit band 時 segment 不晉升 full evidence。
7. partial / resolved counts 與 path_km 累積順序不變。

## 禁止事項
- 不以 AOD550 + Ångström 補造缺波段。
- 不改 CAMS pressure levels。
- 不減 observer LOS segments。
- 不改 Missing ≠ Clear ≠ Zero。
- 不改 Formation / Viewing / Glow branch role。

## Acceptance
- Legacy vs prepared aerosol integrator exact equality。
- Actual CASE Viewing/Glow outputs exact equality。
- Full fresh-extract regression PASS。
- Field CASE 確認 `TWILIGHT_GLOW_COMPONENT_OBSERVER_SPECTRAL_EXTINCTION` 明顯下降後才標 FIELD PASS。
