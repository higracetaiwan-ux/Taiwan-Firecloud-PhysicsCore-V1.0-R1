# Taiwan Firecloud PhysicsCore — Current Project State
## V1.0-R5.7.38

### 現行主線

R5.7.38：**CAMS Post-success Download Recovery**。

### 已 Field Closed

- R5.7.35 Aerosol Scattering Physics Phase 1。
- R5.7.35.1 Aerosol Missing-Reason Handoff。
- R5.7.37 Near-Surface Molecular Boundary Closure：2026-09-10 sunset CASE 已達 Analysis Integrity 61/61 PASS、CASE Integrity 23/23 PASS；100 km / 3.75 km molecular coverage 156/156。

### R5.7.38 解決的問題

R5.7.37 CASE 中，f024 Spectral AOD remote lifecycle 約 21 秒已 successful，但下載遇 502 後 client 等待約 120 秒，使 worker 約 153 秒。本版不重送 remote request，而是對 same request ID 的 Results/location 做有界 download recovery。

### 核心契約

- request ID 不變。
- duplicate submit = 禁止。
- transient HTTP = 408/429/500/502/503/504。
- 預設 attempts=4。
- initial backoff=2 s。
- max backoff=12 s。
- per-attempt HTTP timeout=45 s。
- signed download URL 不持久化。
- exhausted download failure 仍可在下一次 reattach 同一 request ID。

### 目前驗證

- Focused CAMS stateful + download recovery：12/12 PASS。
- Full working-tree regression：542/542 PASS。
- FULL-CLEAN 預封包 extracted regression：542/542 PASS。
- 正式 FULL-CLEAN release gate：CLOSED。
- Field Validation：OPEN。

### 下一步

1. 用 R5.7.38 跑新 CASE。
2. 若再次遇到 transient 5xx，確認同 request ID retry、download elapsed/backoff 與 no duplicate submit。
3. 無 5xx 的 CASE 仍需確認新的 download telemetry/schema 正常輸出。
4. Field validation 完成後，再回到 Canvas Optical Truth / Tier2 / Multiple Scattering 等科學主線。
