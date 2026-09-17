# Implementation Status — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.25.1

## Step 3L.1 Stable Contract Sample Serialization Hotfix

### Implemented
- `STABLE_CONTRACT_SAMPLE_SIGNIFICANT_DIGITS = 8`
- `_stable_contract_sample()`
- Step 3L contract sample-only canonicalization
- FIELD-observed cross-platform variant regression test
- release identity bump to `1.0.0-R5.7.41.3.4.10.25.1`
- README / UI release history update

### Preserved
- `STABLE_EVIDENCE_SIGNIFICANT_DIGITS = 11`
- Step 3L evidence/gate semantics
- full-double habit/roughness optical calculations
- Frozen Science
- runtime habit / roughness fail-close
- `tau_ice` / production promotion fail-close

### QA
- Working-tree regression：894/894 PASS。
- FIELD：pending。
