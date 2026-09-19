# Release Closure Verification — PhysicsCore R5.7.41.3.4.10.30.18.1

## Result
**QA PASS / FIELD pending**

## Scope
CAMS ADS same-request-ID bounded reattach hotfix after `.10.30.18` TWS100 sunrise FIELD failure. Frozen science and Step3Q V1_18 provenance remain unchanged.

## Regression
- CAMS targeted: 28/28 PASS
- New/legacy reattach core subset: 9/9 PASS
- Step3Q lineage: 60/60 PASS
- Full regression: 987/987 PASS
- Failures: 0
- Existing pandas FutureWarning: 1

## Provenance closure
- Step3Q contract: `FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_18`
- Step3Q version: `R5.7.41.3.4.10.30.18`
- evidence SHA256: `8ca8093973d164facfb850509cad6ec06c155d1716aaef3d2ace4976d97987c6` — byte-identical to `.10.30.18`
- gate SHA256: `1d30d22e627d018e12f597ec76249a7dd2845fff0c42374f02e519961ff3377c` — byte-identical to `.10.30.18`
- contract SHA256: `f6dbfbea2a4fa185b0d7d324c69a4432c01764a60fa001d76a00122ca69cb8d6`
- Compared with `.10.30.18` contract, the only top-level difference is `physicscore_version` (`.10.30.18` → `.10.30.18.1`).

## Runtime recovery contract
`R5.7.41.3.4.10.30.18.1_SAME_REQUEST_ID_BOUNDED_REATTACH_V1`

- `TIMEOUT_DEFERRED` is eligible only when durable request ID + recovery eligibility are present.
- Reattach recovery uses the same ADS request ID.
- Reattach-only mode is prohibited from fresh `submit()`.
- Missing journal/request ID or remote recovery failure remains fail-closed.
- Bounded reattach exhaustion remains `TIMEOUT_DEFERRED` / Missing.

## Science guards
- Frozen baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`
- Exact Band24/25 reproduction: blocked
- `TAU_ICE_PRODUCTION_ALLOWED=False`
- `PRODUCTION_ICE_OPTICS_READY=False`
- Step 3R: blocked
