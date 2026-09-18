# Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.30.7 Release Notes

版本：`1.0.0-R5.7.41.3.4.10.30.7`

## Step 3Q.7 — Historical Public Release vs Current Archive Availability Boundary Qualification

本版修正 Step 3Q.6 的 archive provenance 時間語義，不改 Frozen science、Formation、Viewing、Twilight Glow、六波段、Canvas、Dynamic、Earth Shadow 或任何 production gate。

新增定案：
- ARM 2002 proceedings 明確記錄 `RRTM_SW v2.4` 當時已公開發佈並可由 AER 網站取得。
- 2006 JGR radiative-closure study 明確記錄使用 `RRTM_SW v2.5`。
- AER 現行 `RRTMG_SW` README 則指出目前公開 release archive 不提供 Version 5.0 以前 releases。
- 因此必須區分「歷史上曾公開」與「目前仍公開可取得」；current unavailability 不得改寫成 historical non-publication。
- 上述證據仍未恢復 Q. Fu high-resolution pre-averaging tables、band-averaging generator、exact h realization、solar grid 或 discrete weights。

Qualification state：
`PASS_FAIL_CLOSED_HISTORICAL_PUBLIC_RELEASE_EXISTENCE_AND_CURRENT_ARCHIVE_BOUNDARY_QUALIFIED_EXACT_GENERATOR_UNRECOVERED`

Production Ice Optics 仍 fail-close；不得進 Step 3R。
