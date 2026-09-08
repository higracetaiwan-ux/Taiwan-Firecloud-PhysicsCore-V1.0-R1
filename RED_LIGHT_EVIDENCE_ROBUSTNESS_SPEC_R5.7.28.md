# R5.7.28 Red-Light Evidence Robustness 規格

## 問題來源

R5.7.27.1 的 2026-09-08 sunset field CASE 中，CAMS 09Z
`SPECTRAL_COLUMN_AOD` 在 90 秒 wall-clock deadline 後以
`TIMEOUT_DEFERRED` 結束；12Z 同欄位成功。原版因此只有 −5.5°、−6° 的
route rows 有真實多波段 AOD，Analysis Integrity 正確輸出 payload WARN。

## 凍結契約

- Formation = Sun→CloudBase；Viewing = Cloud→Observer；Glow 為獨立第三分支。
- 核心角度維持 0° 到 −6°、每 0.5°，共 13 angles。
- 六波段維持 550／575／600／650／700／750 nm。
- Missing 不得轉成 Clear、Zero 或 N/A。
- 禁止固定 Angstrom、固定 O3、人工 aerosol 與無界 extrapolation。
- Forecast、Observation、Nowcast 不得混合。

## 真實資料單側時間支援

只有同一分析工作已取得的 CAMS forecast snapshot 可成為候選來源。目標
時次缺少至少兩個 provider-native spectral bands 時，程式可選擇最近的
相鄰成功時次，但必須同時滿足：

1. 時間偏移絕對值不超過 CAMS 原生 forecast interval：3 小時；
2. 以相同 `point_id` 對齊完整 route lattice；
3. 候選 row 至少有兩個真實 550／645／670／800 nm provider fields；
4. 只搬移 spectral AOD fields；不得搬移 O3、3D aerosol、cloud、gas 或 geometry；
5. 所有使用 fallback 的 rows 都輸出來源 valid time、signed offset 與 bound。

若任一條件不成立，spectral AOD 維持 Missing。此機制不會新增 provider
request，也不會把 timeout request 改寫成成功；原始 CAMS request audit
仍完整保留。

## 證據分流

Red-Light reference rows 分別輸出：

- `red_light_cloud_evidence_state`
- `red_light_aerosol_evidence_state`
- `red_light_gas_evidence_state`
- `red_light_precipitation_evidence_state`
- `red_light_component_completeness`

Red-Light summary 另輸出 Primary／Extended domain 的 cloud state、aerosol
state、evidence completeness 與 conflict／fallback／missing counts。整體
`red_light_path_state` 仍保留既有判定；新增欄位只讓 root cause 可分辨，
不建立新的 Physics Score。

## 不在本版範圍

- 不修改 cloud evidence conflict 的物理判定。
- 不修改 Canvas、Formation、Photography Decision 或 Viewing gate。
- 不完成 Viewing Full Six-Band RT。
- 不加入 Glow solver、UI angle selector 或 Tier-2 LUT。

