# Taiwan Firecloud PhysicsCore — Release Closure Verification

## Release
`V1.0-R5.7.41.3.4.10.30.7`

## Step
Step 3Q.7 — Historical Public Release vs Current Archive Availability Boundary Qualification

## Scientific correction
- ARM 2002 proceedings：`RRTM_SW v2.4` 當時已公開發佈並可由 AER 網站取得。
- 2006 JGR radiative-closure study：記錄使用 `RRTM_SW v2.5`。
- AER 現行 `RRTMG_SW` README：目前 public release archive 不提供 Version 5.0 以前 releases。
- 因此 historical public existence 與 current public availability 必須分離。
- 這項更正不恢復 historical Fu96 pre-averaging generator，也不允許從 final tables 反解 exact h / solar grid / weights。

## Qualification state
`PASS_FAIL_CLOSED_HISTORICAL_PUBLIC_RELEASE_EXISTENCE_AND_CURRENT_ARCHIVE_BOUNDARY_QUALIFIED_EXACT_GENERATOR_UNRECOVERED`

## Production guards
- exact Fu96 weighting: unavailable
- band 24 exact reproduction: false
- band 25 exact reproduction: false
- band-integrated optical validation ready: false
- tau_ice production allowed: false
- Production Ice Optics ready: false
- physics promotion allowed: false

## Regression
- targeted: 20/20 PASS
- full regression: 950/950 PASS
- existing pandas FutureWarning: 1
- failures: 0
- fresh-extract targeted: 20/20 PASS

## Artifact regeneration
- evidence SHA256: `2f1ea7387ef0742b7663d6917f0d11f1ba0303a2f6e21ff019a291c5e6e214c7` — BYTE-EXACT PASS
- gate SHA256: `5c16c98c0190991f31e188a5a5e4211cb6e30617add777f0fd654d2004d911dc` — BYTE-EXACT PASS
- contract SHA256: `58586ad627f35f7de491f37904ef7057e998510062b3f42f217ce246d8faa395` — BYTE-EXACT PASS

## Decision
**QA PASS / FIELD CASE pending**

Step 3R remains blocked until an authoritative historical Q. Fu high-resolution table set, AER cloud-table preprocessor, equivalent exact generator, or exact band-24/25 numerical reproduction chain is recovered.
