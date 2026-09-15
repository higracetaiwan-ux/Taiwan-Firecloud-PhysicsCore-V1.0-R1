# Implementation Status — V1.0-R5.7.41.3.4.10.11.2

## 狀態

**Dmax Runtime Contract Alignment implemented. Production promotion remains disabled.**

## 程式修正

- `firecloud/ice_cloud_spectral_optics.py`
  - authoritative diagnostic lookup 改為 Dmax-first
  - 移除 r_eff-first lookup
  - positive IWP 缺 Dmax fail-close
  - runtime schema 新增 `ice_maximum_dimension_um` / `ice_optics_lookup_state`
  - contract payload 固定 `primary_size_coordinate=maximum_dimension_um`
  - LUT ordering 改以 Dmax 排序
- `firecloud/case_integrity.py`
  - Ice runtime schema 要求 Dmax
  - contract integrity 驗證 primary size coordinate
  - Portable V1.1 integrity 驗證 Dmax-first
- `firecloud/data/ice_optics/`
  - 納入 certified Portable V1.1 artifact lineage 與 portable LUT serialization
  - bundled artifact 不自動晉升 production/runtime truth

## 科學邊界

`physics_promotion_allowed=false`

本版不修改 Formation / Viewing / Twilight Glow / COT / Red-Light decision。
