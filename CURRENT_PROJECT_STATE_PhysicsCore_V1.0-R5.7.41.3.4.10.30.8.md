# Taiwan Firecloud PhysicsCore — Current Project State

版本：`1.0.0-R5.7.41.3.4.10.30.8`
狀態：`QA PASS / FIELD CASE pending`
Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`

## Step 3Q.8 現況

已正式 qualification 一份外部保存的 RRTM_SW v2.5 distribution lineage：update note、v2.5 makefile、CVS-expanded `cldprop.f`、`taumoldis.f` 均有 pinned commit/blob provenance。

外部 v2.5 `cldprop.f` 與 AER pinned archive 的 science/runtime 內容一致，只差 CVS keyword lines；但因 original AER tarball hash 尚未恢復，external mirror 不能提升為 original-distribution byte identity。

v2.5 `taumoldis.f` 明確存在 low-resolution / high-resolution Kurucz source distinction。因此 runtime SFLUXREF 不能被拿來當未恢復的 cloud-table high-resolution weighting vector。

正式 state：
`PASS_FAIL_CLOSED_V25_EXTERNAL_DISTRIBUTION_LINEAGE_QUALIFIED_PREAVERAGING_GENERATOR_UNRECOVERED`

## 仍缺少

1. original AER v2.5 tarball 或可驗證的原始 archive hash / authenticity chain。
2. Q. Fu high-resolution ice optical pre-averaging tables。
3. historical cloud-table band-averaging preprocessor / generator。
4. exact band-24 mixing realization。
5. band-25 archived-generator identity。
6. exact historical solar spectrum grid / within-band discrete weights。
7. band 24/25 exact numerical reproduction。

## 下一步

優先沿外部 v2.5 distribution 的舊 AER FTP 路徑 `pub/downloads/aer_rrtm_sw`、archive mirrors、研究機構備份或舊 CVS exports 追 original tarball / preprocessor / high-resolution tables。未恢復上述來源前，不進 Step 3R。
