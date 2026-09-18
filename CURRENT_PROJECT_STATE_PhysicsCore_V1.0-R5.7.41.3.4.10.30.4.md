# Taiwan Firecloud PhysicsCore — Current Project State

現行 QA 基線：`V1.0-R5.7.41.3.4.10.30.4`

Step 3Q.4 已將 Fu-lineage `h` domain 明確投影到 RRTMG band 24/25：Chou 1998/2002 對 ice cloud 給出 0.175/0.18–0.700 µm 的 `h=1`，0.700–1.220 µm 的 `h=2/3`。因此 RRTMG band 25（0.441501–0.625000 µm）完整落在 `h=1` domain；band 24（0.625000–0.778210 µm）跨越 0.700 µm 邊界，不能無證據指定單一 `h`。

這些是 Fu-lineage domain constraints，不等同 archived RRTM/RRTMG Fu96 table generator 的 exact provenance。band 25 exact archived-generator identity、band 24 historical mixing realization、pre-averaging samples、exact solar grid/weights與 numeric reproduction 仍未完成。Production Ice Optics 維持 fail-close。
