# RELEASE NOTES — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.23.1

## Step 3J.1 Hotfix

### Fixed

- 修正 CAMS `PRESSURE_LEVEL_CHEMISTRY_OPTICS_BUNDLE` 等 isolated child 已回傳 `TIMEOUT_DEFERRED`，但 `cams_worker_checkpoints.json` 仍殘留 `STARTED/RUNNING` 的證據鏈不一致。
- child `TIMEOUT_DEFERRED` 現在會寫入 durable terminal checkpoint，保存 exit code、error 與 worker file provenance。
- Step 3J diagnostic evidence 使用 16 significant digits 的穩定序列化，消除不同平台最後 1 ULP 造成的 byte drift。

### Not changed

- 不改 `β_ext` / `k_ext` 原始計算。
- 不改 Wyser PSD、Yang/Bi kernel、grid convergence 或 mass closure。
- 不計算 production `tau_ice`。
- 不指定 runtime habit / roughness。
- 不改 Formation / Viewing / Twilight Glow / Frozen Science。

### Validation

- related focused regression: 83/83 PASS
- working-tree full regression: 874/874 PASS
- FIELD validation: pending
