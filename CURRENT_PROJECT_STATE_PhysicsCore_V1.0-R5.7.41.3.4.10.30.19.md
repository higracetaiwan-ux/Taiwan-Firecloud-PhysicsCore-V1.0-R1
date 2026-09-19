# Taiwan Firecloud PhysicsCore V1.0 — Current Project State

## 現行 QA 版本
`1.0.0-R5.7.41.3.4.10.30.19`

## Science baseline
`R5.7.41.2_SHADOW_COT_AB_FROZEN`

## Step 3Q
**Step 3Q.19 — Fu Primary-Band Forward-Reconstruction Input Qualification**

正式狀態：`PASS_FAIL_CLOSED_FU96_PRIMARY_BAND_FORWARD_RECONSTRUCTION_INPUTS_QUALIFIED_RRTMG_FINE_GRID_AND_EXACT_BAND24_25_REALIZATION_UNRECOVERED`

已恢復：Fu Eq.3.9 primary-band coefficient input set（90 values）、可執行 primary-band forward model、RRTMG forward process class。

尚未恢復：exact fine spectral grid / interpolation realization、historical discrete solar weights、high-resolution pre-averaging samples，因此 Band24/25 exact reproduction 與 Production Ice Optics 仍 fail-close。

最新 FIELD baseline（在本版 FIELD 前）：`R5.7.41.3.4.10.30.18.2 FIELD PASS`。
