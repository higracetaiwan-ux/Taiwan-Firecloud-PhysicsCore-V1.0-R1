# R5.7.41.3.3 — Historical Replay Empty Cloud-Volume Guard Hotfix Spec

## Field trigger
2026-08-30 歷史回測三次皆在 Twilight Glow 的 Cloud→Observer spectral extinction 階段失敗：
`KeyError: 'direction_offset_deg'`。

Trace 指向 `firecloud/viewing_spectral.py::_cloud_expected_tau()`。當歷史 provider/replay 回傳 headerless empty cloud-layer DataFrame 時，程式仍直接讀取 `cand["direction_offset_deg"]`，造成 analysis worker 終止。

## Frozen semantics
- Missing != Clear != Zero。
- Headerless/empty/malformed cloud-volume evidence 不可推論為晴空。
- 真正 schema 完整但該 target route 無 blocker row，才可保留 `VIEW_CLOUD_PATH_CLEAR`。
- 本 hotfix 不修改 Formation、Viewing extinction 公式、Production/Shadow COT、Glow 或 Photography science。

## New fail-closed state
`VIEW_CLOUD_VOLUME_UNRESOLVED`

觸發條件：
- cloud-layer DataFrame 為 None 或 empty；或
- 缺少 `direction_offset_deg`, `distance_km`, `z_base_km`, `z_top_km` 任一必要欄位；或
- prefiltered cloud group 本身失去必要 schema。

此狀態：
- cloud tau = Missing
- total six-band transmission = Missing（若 CLOUD component 不完整）
- analysis 繼續完成，不得因 KeyError 終止。

## Regression requirements
1. headerless empty cloud frame 不 crash且 fail-close。
2. malformed non-empty frame 缺 direction schema 不 crash且 fail-close。
3. full viewing builder 保留 partial/missing evidence，不生成假的 total transmission。
4. 完整 cloud schema、但 target route 沒有 blocker 時仍可判 PATH_CLEAR。
