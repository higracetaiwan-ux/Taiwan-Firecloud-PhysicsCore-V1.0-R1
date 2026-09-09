# PhysicsCore V1.0-R5.7.29 Implementation Status

## Completed

- [x] Viewing Full Six-Band RT component closure
- [x] Partial component fail-closed semantics
- [x] time + angle + target evidence identity
- [x] native hydrometeor merge → Viewing snapshot wiring
- [x] explicit local-target unresolved coverage
- [x] six-band summary → Photography diagnostic handoff
- [x] five Analysis Integrity guards
- [x] three Viewing RT CASE required members
- [x] targeted regression：32 passed / 0 failed
- [x] full working-tree regression：473 passed / 0 failed
- [x] R5.7.28 CASE replay：484/484 targets；13/13 Photography；0 categorical changes
- [x] FULL-CLEAN extraction regression：473 passed / 0 failed

## Field validation required

以 R5.7.29 真實部署重新產生 sunset CASE，確認：

- Viewing precipitation evidence 不再是空表，且 provenance 指向 native
  RWMR/SNMR/GRLE；
- 五項 `VIEWING_SIX_BAND_*` Integrity checks 依真實資料得到 PASS，或對真實
  provider gap 明確保持 Partial/Missing；
- Full rows 的六波段 total tau 與 transmission arithmetic closure 通過；
- Formation/Photography 13-angle 與 Formation-first dominance 不變。

未完成 field validation 前，不宣稱特定 sunset CASE 一定能得到 Full RT；真實
provider evidence 不完整時，Partial/Missing 是正確結果。

