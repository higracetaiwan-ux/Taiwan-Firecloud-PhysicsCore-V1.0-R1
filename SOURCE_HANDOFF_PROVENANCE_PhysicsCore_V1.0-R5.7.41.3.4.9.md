# Source Handoff Provenance — PhysicsCore V1.0-R5.7.41.3.4.9

## Source baseline
直接由已驗證的 `V1.0-R5.7.41.3.4.8 FULL-CLEAN` 工作樹延續。

## 本版 source changes
- `firecloud/red_light_availability.py`：新增 profiler-only timing side channel。
- `firecloud/model.py`：把 component rows 匯入 performance diagnostics。
- `firecloud/__init__.py`：版本更新。
- `app.py`：版本鏈更新。
- tests：新增 `.3.4.9` profiler contract，舊版本斷言同步更新。
- release/state/spec/test docs：新增 `.3.4.9` 文件。

## 不宣告的事項
本版不宣告 Red-Light 已加速，也不宣告任何 Red-Light science 改善。Field profiler 尚未完成前，唯一目的為 runtime hotspot decomposition。
