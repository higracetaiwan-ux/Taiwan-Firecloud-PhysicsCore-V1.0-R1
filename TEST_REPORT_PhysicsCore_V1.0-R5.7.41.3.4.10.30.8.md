# Test Report — 1.0.0-R5.7.41.3.4.10.30.8

## Targeted regression

Step 3Q / 3Q.1–3Q.8 / integrity / handoff：**26/26 PASS**。

## Full regression

互斥分批執行：
- 146 PASS
- 169 PASS
- 148 PASS
- 97 PASS
- 63 PASS
- 89 PASS
- 71 PASS
- 116 PASS
- 55 PASS

Total：**954/954 PASS**

既有 warning：1 個 pandas `FutureWarning`；非 failure。

## Release artifacts

- evidence SHA256：`5bb874e1b4ef1ca7e3a389978886021b9e7fe65749e624eb969531c9f2d5cecc`
- gate SHA256：`6db1d034e36840a5615d80b4ce622c60d047fe4036f112ecfab2925c523f41d9`
- contract SHA256：`71365fee9cc7967aca79ff3731a0ff609a1800c1363afb2228aea5b4ede12463`

Fresh-extract targeted：**26/26 PASS**。

Fresh regeneration byte-exact：evidence / gate / contract 全部 PASS。
