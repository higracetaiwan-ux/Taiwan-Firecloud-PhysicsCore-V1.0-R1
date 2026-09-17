# Ice Microphysics Step 3L — Yang/Bi Habit + Roughness Qualification

版本：`R5.7.41.3.4.10.25`  
Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`  
狀態：**QA PASS / FIELD VALIDATION PENDING**

## 目的
Step 3L 將「habit model-family bridge」與「runtime habit/roughness inference」正式分離。Wyser solid-column lineage 可對應 Yang/Bi V2 的 `single_column` model family，但這不代表 exact geometry equivalence，也不代表 GFS 能預報真實 habit。

## Authoritative inventory
- TAMU/Yang-Bi V2 bundled LUT：9 habits × 3 roughness states × 189 Dmax × 6 Firecloud bands = **30,618 rows**。
- Roughness source states：`Rough000 / Rough003 / Rough050`。
- Particle-size domain：2–10,000 µm；Step 3L 不建立任何 hidden habit/roughness interpolation。

## Qualification result
```text
WYSER_YANG_SOLID_COLUMN_HABIT_FAMILY_BRIDGE_PASS = true
EXACT_GEOMETRY_EQUIVALENCE_PASS                  = false
GFS_NATIVE_HABIT_INFERENCE_PASS                  = false
ROUGHNESS_ENSEMBLE_DIAGNOSTIC_READY              = true
RUNTIME_HABIT_DEFAULT_ALLOWED                    = false
RUNTIME_ROUGHNESS_DEFAULT_ALLOWED                = false
TAU_ICE_PRODUCTION_ALLOWED                       = false
PRODUCTION_ICE_OPTICS_READY                      = false
physics_promotion_allowed                        = false
```

## Optical sensitivity
Source-row uncertainty 顯示 habit 與 roughness 都不能靜默忽略：
- habit mass-extinction max relative spread：`3.4915863464`；max |Δg|：`0.1989`。
- single-column roughness mass-extinction max relative spread：`0.055665051279`；max |Δg|：`0.0325`。
- single-column three-roughness PSD-weighted bulk ensemble：max `k_ext` spread `0.29651018881 m²/kg`；max `g` spread `0.016970705674`。

因此 `single_column` 只取得 model-family semantic bridge；`Rough000/Rough003/Rough050` 只作 uncertainty ensemble，不選 production truth/default。

## Frozen
Formation / Viewing / Twilight Glow / six bands / Canvas-Corridor-REZ / Earth Shadow / Production-Shadow COT / Step 3J-3K science / Ice runtime promotion semantics 全部不變。
