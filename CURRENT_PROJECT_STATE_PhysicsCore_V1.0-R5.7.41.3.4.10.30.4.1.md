# Taiwan Firecloud PhysicsCore — Current Project State

## 現行版本
`1.0.0-R5.7.41.3.4.10.30.4.1`

## 狀態
Step 3Q.4 integrity contract matcher hotfix。

本版只修正 `case_integrity.py` 對 Step 3Q.4 contract version 的辨識：
- 正確接受 `FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_4`
- 正確接受 `PASS_FAIL_CLOSED_H_DOMAIN_CONSTRAINTS_QUALIFIED_RRTMG_EXACT_H_UNRESOLVED`

Science baseline 保持 `R5.7.41.2_SHADOW_COT_AB_FROZEN`。
Step 3Q.4 evidence / gate / contract 科學內容不變。
Production Ice Optics 仍 fail-close。
