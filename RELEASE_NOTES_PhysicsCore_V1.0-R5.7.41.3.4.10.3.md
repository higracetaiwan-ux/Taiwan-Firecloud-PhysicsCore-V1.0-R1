# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.3

## 名稱
Twilight Glow Observer Precipitation Horizontal-Support Ray Reuse

## 變更
- `firecloud/precipitation.py`
  - 新增 `_integrate_view_path()`。
  - Cloud→Observer precipitation path 對同一 horizontal support 共用一次 17-point curved-Earth LOS。
  - 垂直 hydrometeor layers 仍逐層 intersection / Missing / tau accumulation。
- 版本提升為 `1.0.0-R5.7.41.3.4.10.3`。
- 新增 exact-equivalence 與 ray-call-count tests。

## Field evidence 起點
`.3.4.10.2 TWS134`：Observer Precipitation = **14.309378 s**，為 Glow 第一大 component。

## Science
無 science threshold、weight、spectral band、hydrometeor physics、Formation/Viewing/Glow decision 變更。
