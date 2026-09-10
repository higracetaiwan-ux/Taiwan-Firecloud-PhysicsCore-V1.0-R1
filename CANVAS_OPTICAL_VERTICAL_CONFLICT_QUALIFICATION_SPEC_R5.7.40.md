# R5.7.40 Canvas Optical Vertical Conflict Qualification 規格

## 目的

R5.7.39.1 真實 CASE 已證明 pgrb2b provider 可正常取得中間 pressure levels；同 CASE 的 432 個 Formation Canvas 仍為 `CF_CLOUD_CONDENSATE_ZERO`。R5.7.40 不直接補 COT，而是先判定這些衝突在原生垂直資料中的型態。

## 資料角色

- 主 `pgrb2.0p25`：cloud-fraction geometry、CLWMR、ICMR、HGT/TMP/RH pressure-level state。
- `pgrb2b.0p25`：125/175/225…925 hPa 的中間層 CLWMR、ICMR、HGT、TMP hydrometeor context。
- `pgrb2b` pressure-level cloud fraction 不作幾何或 COT 判定。NCEP pgrb2b inventory 的中間 isobaric records提供 HGT/TMP/RH 與 CLWMR/ICMR 等 hydrometeor，並未列 pressure-level TCDC。

## 分類

1. `ISOLATED_PRIMARY_CF_SPIKE_HYDROMETEOR_UNSUPPORTED`：主衝突層 CF>clear threshold 且 condensate=0；上下主鄰層為 clear+zero；兩側最近 pgrb2b 中間 hydrometeor 也為 native zero。
2. `INTERMEDIATE_NATIVE_CONDENSATE_SUPPORT_PRESENT`：至少一側 pgrb2b 中間層存在 native positive CLWMR/ICMR。
3. `ADJACENT_PRIMARY_NATIVE_CONDENSATE_SUPPORT_PRESENT`：相鄰主 pgrb2 pressure level 存在 native positive condensate。
4. `PRIMARY_CF_SIGNAL_WITH_ZERO_INTERMEDIATE_HYDROMETEORS`：中間層為 zero，但主鄰層 cloud-fraction context 不是完整 clear-zero 孤立條件。
5. `VERTICAL_CONTEXT_INCOMPLETE`：主鄰層或中間 hydrometeor evidence Missing/不完整。

## 不可做的事

- 不由 RH 生成 condensate。
- 不由 cloud fraction 生成 condensate 或 COT。
- 不把 intermediate positive condensate 自動升格 target COT READY。
- 不改 Canvas membership、Formation、Viewing、Glow、Photography。
- Missing != Zero != Clear。

## CASE / Integrity

新增：
- `v1_canvas_vertical_conflict_qualification.csv`
- `v1_canvas_vertical_conflict_qualification_summary.csv`
- `CANVAS_OPTICAL_VERTICAL_CONFLICT_QUALIFICATION`
- `CANVAS_OPTICAL_VERTICAL_CONFLICT_SUMMARY`

若 pgrb2b probe 已 READY 且存在 primary conflict Canvas，資格表必須覆蓋所有 conflict Canvas；任何 target COT/Formation promotion 欄位都使 Integrity FAIL。
