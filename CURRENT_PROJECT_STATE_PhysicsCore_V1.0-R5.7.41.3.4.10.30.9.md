# Taiwan Firecloud PhysicsCore — Current Project State

版本：`1.0.0-R5.7.41.3.4.10.30.9`
Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`
目前 Step：**3Q.9**

## 現況
- v2.5 external distribution lineage：qualified
- external mirror GitHub import time（2020）與 historical AER CVS source time（2004）：已正式分離
- AER official RRTM_SW runtime Kurucz context：qualified
- runtime solar context ≠ unrecovered Fu cloud-table high-resolution weight vector：正式 fail-close
- historical pre-averaging generator：仍未恢復

正式 state：
`PASS_FAIL_CLOSED_V25_MIRROR_TIME_AND_RUNTIME_SOLAR_CONTEXT_QUALIFIED_PREAVERAGING_GENERATOR_UNRECOVERED`

## 下一個 blocker
優先尋找：
1. original AER v2.5 archive / hash / mirror authenticity chain；
2. `/storm/rc1/cvsroot/rc/rrtm_sw/` 相關 CVS attic / preprocess code；
3. Q. Fu high-resolution cloud optical tables；
4. historical cloud-table band averaging generator；
5. band 24/25 exact reproduction 所需的 spectrum/grid/weights。

在上述資料不足前，不進 Step 3R，不產生 production `tau_ice`。
