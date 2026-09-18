# Taiwan Firecloud PhysicsCore — Current Project State

現行 QA 基線：`V1.0-R5.7.41.3.4.10.30.3`

Step 3Q.3 已把 historical Fu-lineage coalbedo averaging equation family 固定為可驗證 provenance：solar-weighted linear、solar-weighted logarithmic，以及由 empirical `h` 混合的 effective coalbedo。真正剩餘 blocker 已進一步縮小為：RRTM/RRTMG archived default Fu96 band 24/25 table generation 所用的 band-specific `h`（或完全等價的 historical generator）、pre-averaging spectral samples、exact solar spectrum/grid/discrete weights，以及最終 numeric reproduction。

Production Ice Optics 仍 fail-close。
