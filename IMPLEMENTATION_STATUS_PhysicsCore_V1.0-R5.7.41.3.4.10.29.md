# Taiwan Firecloud PhysicsCore — IMPLEMENTATION STATUS

## 現行開發版本
`1.0.0-R5.7.41.3.4.10.29` — **QA CANDIDATE / FIELD VALIDATION PENDING**

## 最新正式 FIELD baseline
`R5.7.41.3.4.10.28.1 FIELD PASS`

## Step 3P
本版新增 Yang/Bi V2 Full-Spectral Source Capability Qualification。Authoritative contract 已固定為 396 wavelengths、189 particle sizes；只資格化 `single_column × Rough000/Rough003/Rough050`。

FULL-CLEAN 不攜帶大型 `Data_0.2_15.25` source archive，因此 release evidence 明確為 `SOURCE_BYTES_UNAVAILABLE`。這不是 Clear/Zero，也不是 validation failure；它表示 band 24/25 full-spectrum coverage 尚未在本 release 環境執行。

## Frozen gates
- 六波段 portable LUT 不得插值補造成 396-wave source。
- Exact Fu96/RRTMG band weighting：未證明。
- Independent SSA validation：False。
- Independent asymmetry validation：False。
- Full six-band like-for-like optical validation：False。
- tau_ice production：False。
- Production Ice Optics：False。
- physics promotion：False。
