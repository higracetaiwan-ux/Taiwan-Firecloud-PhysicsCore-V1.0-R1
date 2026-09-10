# Taiwan Firecloud PhysicsCore V1.0-R5.7.38 實作狀態

## 已完成

- CAMS terminal-success 與 download phase 分離。
- same-request-ID Results/location refresh。
- transient HTTP/connection bounded retry。
- Retry-After 本地上限保護。
- client-native fallback 僅允許單次。
- download journal telemetry，且不寫入 signed URL。
- exhausted download failure 保留 recovery eligibility。
- Analysis Integrity 新增 `CAMS_POST_SUCCESS_DOWNLOAD_RECOVERY_TELEMETRY`。
- 新增 retry、no-duplicate-submit、404 fail-close、120 秒 Retry-After cap、URL privacy、Integrity regression tests。

## Regression

目前 working tree：**542/542 PASS**。

FULL-CLEAN 預封包解壓後：**542/542 PASS**。

## 發行封裝

- 正式 FULL-CLEAN ZIP：已完成。
- ZIP hygiene：0 cache/pyc。
- extracted ZIP 全 regression：542/542 PASS。
- SHA256：已產生。

## 尚待

- R5.7.38 新 CASE field validation。

## 不處理範圍

本版不處理多重散射、絕對輻射校正、Canvas COT calibration 或 Formation 權重，也不改任何科學門檻。
