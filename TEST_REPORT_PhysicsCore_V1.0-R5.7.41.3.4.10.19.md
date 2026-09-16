# Test Report — PhysicsCore V1.0-R5.7.41.3.4.10.19

## TDD / working tree
- Step 3F RED：module missing，測試正確失敗。
- Step 3F GREEN：7/7 PASS。
- Targeted regression：81/81 PASS。
- Working-tree full regression：828/828 PASS，0 failed。
- Existing warning：1 pandas FutureWarning。

## Step 3F serialization probe
- evidence：10 rows / 5551 bytes
- gate：1 row / 1233 bytes
- contract：2649 bytes
- Archive-content gates：3/3 PASS

## First packaged fresh-extract
- Extracted version：`1.0.0-R5.7.41.3.4.10.19`
- Group 1：265 PASS
- Group 2：365 PASS；1 existing pandas FutureWarning
- Group 3：198 PASS
- Total：**828/828 PASS**
- Failures：0

Final ZIP is repackaged after this report update and receives a second fresh-extract verification before delivery.
