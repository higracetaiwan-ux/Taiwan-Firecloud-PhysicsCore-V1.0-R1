# Test Report — V1.0-R5.7.41.3.4.10.4

## Targeted

- Gas sigma memo + six-band Viewing/Glow targeted：15/15 PASS。
- LUT content signature content-scoped test：PASS。
- cache-off vs cache-on exact `_integrate_view_gas()` tuple equality：PASS。
- repeated state `_sigma_fast()` calls：36 legacy calls → 18 cached calls in deterministic fixture：PASS。

## Actual TWS134 isolated benchmark

- Glow targets：1092
- gas segments：8736
- exact T/P states：264
- actual gas helper legacy：1.601 s
- actual gas helper memo：0.509 s
- speedup：約 3.14×
- 1092/1092 exact equality：PASS
- sigma cache entries：4752
- spectroscopy LUT content signatures：1

Full observer spectral isolated A/B：output CSV SHA256 identical；約 3.24 → 2.17 s。

## Full regression

- Working tree：**668/668 PASS**
- Existing pandas FutureWarning：1（非 failure）
- Final FULL-CLEAN fresh-extract：**668/668 PASS**
- Existing pandas FutureWarning：1（同既有 warning，非 failure）
- `firecloud/*.py` 與 `.10.3` hash 比對：80 modules 中僅 `__init__.py` 與 `viewing_spectral.py` 變更，其餘 78/80 byte-identical。
