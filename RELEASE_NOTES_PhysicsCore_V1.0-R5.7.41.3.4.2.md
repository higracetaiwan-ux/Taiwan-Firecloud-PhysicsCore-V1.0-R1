# Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.2

## GFS Cloud-Liquid Alias Compatibility Hotfix

本版延續 R5.7.41.3.4.1，修正歷史 NOAA GFS AWS `.idx` 的 Cloud Mixing Ratio variable naming compatibility。

### Field evidence
2026-08-30 Sunrise TWS175：
- NOMADS pgrb2: HTTP 403;
- AWS fallback: `OK_AWS_IDX_RANGE`;
- 182 messages / 45 range requests / ~87.5 MB，完整物件約 541 MB;
- ICMR 22 pressure levels ready; CLWMR 0 pressure levels;
- pgrb2b AWS fallback READY;
- Analysis Integrity / CASE Integrity PASS。

### 修正
- `CLMR` 與 `CLWMR` 只在 transport/decode 名稱層 canonicalize 成相同 native liquid-cloud-water field；
- 新增 raw/canonical index variable audit metadata；
- archive 若沒有任一名稱，仍保持 Missing。

不改 science baseline、COT、Formation、Viewing、Glow、Photography。
