# Release Notes — R5.7.41.3.4.10.30.4.1

## 類型
Integrity hotfix；無 science change。

## 修正
`.10.30.4` FIELD CASE 顯示 `case_integrity.py` 仍要求 Step 3Q contract V1_3，
導致合法的 V1_4 / Step 3Q.4 fail-close state 被誤判為 FAIL。

本版：
- 將 contract matcher 更新為 V1_4。
- 保留現行 Step 3Q.4 fail-close state。
- 新增 regression test。
- 不改 Formation / Viewing / Twilight Glow / Ice Optics science gate。
- 不解鎖 `tau_ice` 或 Production Ice Optics。
