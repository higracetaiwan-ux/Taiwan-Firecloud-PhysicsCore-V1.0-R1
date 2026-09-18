# Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.30.6 Release Notes

版本：`1.0.0-R5.7.41.3.4.10.30.6`

## Step 3Q.6 — RRTM/RRTMG Public Archive Availability Boundary Qualification

本版只補強 Fu96/RRTM/RRTMG historical provenance，不改 Frozen science、Formation、Viewing、Twilight Glow、六波段、Canvas、Dynamic、Earth Shadow 或任何 production gate。

新增定案：
- AER `RRTMG_SW` 公開 README 明確指出目前公開 release 為 Version 5.0，Version 5.0 以前 releases 不公開。
- 公開 `RRTM_SW` pinned runtime archive 保存的是 post-averaged `EXTICE3/SSAICE3/ASYICE3/FDLICE3` 與 Dge interpolation，不包含 Q. Fu high-resolution pre-averaging spectral tables / historical generator。
- 公開舊版 release 缺失本身不得被拿來推論 exact generator identity。
- final runtime tables 仍不得反解唯一 historical h、solar grid 或 discrete weights。

Qualification state：
`PASS_FAIL_CLOSED_PUBLIC_ARCHIVE_AVAILABILITY_BOUNDARY_QUALIFIED_EXACT_GENERATOR_UNRECOVERED`

Production Ice Optics 仍 fail-close。
