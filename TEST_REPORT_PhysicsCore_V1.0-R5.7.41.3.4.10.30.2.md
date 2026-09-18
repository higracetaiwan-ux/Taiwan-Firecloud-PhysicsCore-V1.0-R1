# TEST REPORT — PhysicsCore V1.0-R5.7.41.3.4.10.30.2

## Regression
- Full suite executed as four mutually exclusive batches due single-run execution ceiling.
- Batch 0: 222 PASS
- Batch 1: 267 PASS
- Batch 2: 208 PASS (1 existing pandas FutureWarning)
- Batch 3: 243 PASS
- Total: **940/940 PASS**

## Step 3Q.2 targeted
- historical Fu96 mixed linear/log coalbedo semantic: PASS
- later Yi2013 formula kept separate from historical generator: PASS
- pre-v4 Kurucz runtime context pinned without generator equivalence: PASS
- exact historical weights remain fail-close: PASS
- production gates remain false: PASS
