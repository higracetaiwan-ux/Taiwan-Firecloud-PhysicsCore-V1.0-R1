# TWS106 Near-field Diagnostic Proxy Validation

> 注意：這是利用 `.10.9.1` 舊 CASE 已封存資料進行 `.10.9.3` diagnostic-only 離線重算，不是 `.10.9.3` 新 Field run，因此不能取代正式 FIELD PASS。

## CASE

- Site: TWS106 高美濕地
- Event: 2026-09-14 sunset
- Ground Truth image time: 17:07:49
- Proxy route time: 18:00 hourly route state
- Native comparison: solar altitude 0° native cloud columns

## Ground Truth

實景顯示觀測方向有廣泛、破碎但覆蓋顯著的低層雲幕。影像本身不提供精確距離與雲底高度，因此不從影像反推 5/20/50 km 或 COT。

## Diagnostic output

45 個 0–100 km route points：

- Native low-cloud geometry points: 0
- −5° Extended >40–100 km: coarse mean 22.0%, max 33%
- 0° Extended >40–100 km: coarse mean 26.8%, max 38%
- +5° Extended >40–100 km: coarse mean 42.7%, max 58%

主要 mismatch：

`COARSE_LOW_CLOUD_PRESENT_NATIVE_3D_NOT_RECONSTRUCTED`

## 解讀

此狀態只表示：coarse low-cloud forecast 有低雲訊號，而 native condensate reconstruction 在目前 threshold 下沒有建立 0–100 km low-cloud geometry。

不得解讀為：

- coarse CF 一定正確；
- native 一定錯；
- 直接存在某個 τ；
- 必定是 illumination blocker；
- 必定形成或不形成火燒雲。

## `.10.9.2` Integrity re-evaluation

TWS106 `.10.9.1` 舊 CASE原本因 zero-target semantic-migration 空表出現 3 個 Shadow Collection false FAIL，連帶 Overall FAIL。

套用 `.10.9.2` audit semantics 後：

- SHADOW_COLLECTION_NO_PRODUCTION_SWITCH = PASS
- SHADOW_COLLECTION_NO_PROMOTION = PASS
- SHADOW_COLLECTION_PRODUCTION_SOURCE_FROZEN = PASS
- CASE Integrity = **32/32 PASS**

沒有產生任何 Canvas/COT evidence。
