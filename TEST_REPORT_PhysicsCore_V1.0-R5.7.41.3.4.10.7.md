# Test Report — V1.0-R5.7.41.3.4.10.7

## Targeted regression

- Shared hydrometeor context exactness/reuse + adjacent Viewing/Glow/precipitation chain：**33/33 PASS**
- Prepared route context vs direct route preparation: `check_dtype=True, check_exact=True`.
- Supplied Glow context prevents repeated native hydrometeor preparation.

## Full working-tree regression

The environment has a single-command execution ceiling, so the complete test suite was partitioned into two mutually exclusive test-file groups:

- Group A：**396/396 PASS**，1 existing pandas FutureWarning
- Group B：**287/287 PASS**
- Combined：**683/683 PASS**

No test was omitted; `pytest --collect-only -q` collected 680 tests.

## FULL-CLEAN fresh-extract gate

- Quarter 1: 160/160 PASS
- Quarter 2: 179/179 PASS
- Quarter 3: 166/166 PASS, 1 existing pandas FutureWarning
- Quarter 4: 178/178 PASS
- Combined: **683/683 PASS**
