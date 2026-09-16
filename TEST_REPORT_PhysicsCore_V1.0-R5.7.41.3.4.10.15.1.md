# TEST REPORT — R5.7.41.3.4.10.15.1

## Targeted regression
Relevant Step 3B / Phase 2 / Global Candidate / CASE evidence tests：
**22/22 PASS**

Includes an exact regression fixture for the `.10.15` TWS100 failure:
- member exists
- evidence rows = 0
- gate rows = 0
- contract bytes = 2 (`{}`)

Expected result in `.10.15.1`:
all three new archive-content checks = **FAIL**.

Normal payload fixture:
- evidence rows >= 8
- gate rows >= 1
- contract bytes > 2

Expected result:
all three new archive-content checks = **PASS**.

## Full working-tree regression
**800/800 PASS**
- failed: 0
- warning: 1 existing pandas FutureWarning

## Science regression scope
No changes to Frozen Science. Ice mapping/production remain fail-closed.

## Fresh-extract regression
First packaged FULL-CLEAN fresh extract：**800/800 PASS**，0 failed，1 existing pandas FutureWarning。
