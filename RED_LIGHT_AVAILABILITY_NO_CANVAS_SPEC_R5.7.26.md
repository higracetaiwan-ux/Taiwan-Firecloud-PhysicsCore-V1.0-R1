# R5.7.26 Red-Light Availability 與 No-Canvas 物理契約

## 目的

R5.7.26 正式把下列物理事實分離：

1. **Red-Light Availability**：紅橘直接太陽光是否有能力抵達前方 Primary / Extended Canvas 區域。
2. **Effective Canvas Availability**：0–40 km Primary Canvas 與 40–100 km Extended Canvas 是否真的存在可受光雲體。
3. **Canvas Optical Response**：存在的目標雲是否有足夠 native/secondary optical truth，可計算雲體的六波段方向性回應。
4. **Viewing**：已形成的雲光是否能沿 Cloud→Observer 被攝影者看見。
5. **Glow**：大氣暮光／霞光的獨立第三分支；不能取代 Firecloud Formation。

凍結關係：

`Red-Light Availability != Firecloud Formation != Viewing != Glow`

真正的 Formation 仍需：

`Red-Light Availability × Effective Canvas Availability × Canvas Optical Response`

## Reference Receiver

沒有實際 Canvas 時，不能以「沒有 CloudBase target」作為理由，完全不回答紅光通道是否可用。因此 R5.7.26 新增 **Reference Receiver**。

Reference Receiver：

- 不是實際雲體；
- 不加入 `v1_canvas_candidates`；
- 不建立 COT、phase、r_eff 或雲輻亮度；
- 只代表「假設此處存在一個合適雲底，Sun→此處的直接六波段光路是否可解析」。

預設採樣：

- direction offset：−5° / 0° / +5°；
- Primary：10 / 20 / 30 / 40 km；
- Extended：60 / 80 / 100 km；
- 參考雲底：4 / 5 / 8 / 12 km；
- 光譜：550 / 575 / 600 / 650 / 700 / 750 nm。

這些 reference surfaces 只用於物理診斷，不縮減正式 13-angle Formation 幾何，也不取代真實 Canvas。

## Red-Light Path 證據

每個 reference receiver 必須依序通過：

- finite-solar-disk `DirectSolarFraction`；
- Gas / O₂ / H₂O / O₃ six-band path；
- CAMS aerosol six-band path；
- upstream CloudScene optical blocker path；
- forecast-native 3-D hydrometeor / precipitation path。

任何 critical path 未解析，維持 `UNKNOWN / CONFLICT / PARTIAL`，不得因為「畫面看起來晴朗」或 surface precipitation=0 就假設 Full clear。

Reference path 狀態：

- `NO_DIRECT_RED_ACCESS`
- `RED_LIGHT_PATH_OPEN`
- `RED_LIGHT_PATH_PARTIAL`
- `RED_LIGHT_PATH_ATTENUATED`
- `RED_LIGHT_PATH_CONFLICT`
- `RED_LIGHT_PATH_UNKNOWN`

`OPEN` 是 evidence-complete 的結構狀態，不代表「沒有分子／氣膠衰減」。Gas/Aerosol attenuation 仍保留在六波段 transmission 與 availability 中。

## No-Canvas 狀態

只有在 `CLOUD_GEOMETRY` completeness 完整時，0 個 Canvas candidates 才能被判為 `ABSENT / NO_CANVAS`；若雲幾何本身不完整，必須輸出 `CANVAS_AVAILABILITY_UNKNOWN`。

當 Primary 與 Extended Canvas 均確認無有效 target：

- `SPECTRAL_AEROSOL_PATH = NOT_APPLICABLE`
- `SPECTRAL_CLOUD_PATH = NOT_APPLICABLE`
- `FULL_SPECTRAL_RT = NOT_APPLICABLE`

原因為 `NO_TARGET_CLOUD_GEOMETRY`，而非 Missing。

Red-Light path 與 no-Canvas 組合後可輸出：

- `CLEAR_RED_PATH_NO_CANVAS`
- `PARTIAL_RED_PATH_NO_CANVAS`
- `RED_PATH_ATTENUATED_NO_CANVAS`
- `NO_CANVAS_NO_DIRECT_RED_ACCESS`
- `NO_CANVAS_RED_PATH_CONFLICT`
- `NO_CANVAS_RED_PATH_UNKNOWN`

其中 `CLEAR_RED_PATH_NO_CANVAS` 明確代表：

> 紅光路徑可用，但目前 0–100 km 沒有有效雲畫布，因此沒有 Firecloud Formation。

它不是 `FIRECLOUD_FORMED`，也不是 `DATA INCOMPLETE`。

## Unused Red-Light Potential

`Unused Red-Light Potential` 是 reference receivers 的連續六波段後 RT 診斷量，現在標記為：

`CONTINUOUS_UNCALIBRATED_DIAGNOSTIC`

它：

- 不是 Physics Score；
- 不是 Firecloud probability；
- 不設定 HIGH / MEDIUM / LOW 生硬門檻；
- 只用來表示「如果此時有合適 Canvas，可利用的紅光場大約有多少」。

目前 red diagnostic mean 使用 600 / 650 / 700 / 750 nm；550 與 575 nm 仍完整保留在 six-band evidence，不會被刪除或提前降維。

## Forecast / Observation 邊界

2026-09-08 高美濕地實拍顯示強烈橙紅 twilight glow，可作後續 Ground Truth / Observation validation；但 Observation 不得回寫成事前 Forecast input。

如果 Forecast cloud/condensate evidence 存在 conflict，R5.7.26 必須輸出 `RED_LIGHT_PATH_CONFLICT/UNKNOWN`，不能因實拍事後證明天空乾淨，就假裝預報當時已有完整證據。

## Headline / Legacy Score

若無 Canvas：

- legacy `physics_score` 可留在 CASE 供歷史相容；
- `legacy_physics_score_applicable = False`；
- `core_score_eligible = False`；
- 已解析的 no-Canvas context 可取代舊 `UNKNOWN / DATA INCOMPLETE` headline。

這不恢復單一分數架構。Formation / Viewing / Glow 繼續永久分離。
