# Test Report — V1.0-R5.7.41.3.4.10.5

## `.10.4` Field confirmation

- TWS134 live Observer Spectral Extinction：8.532848 → 6.642360 s（−22.2%）。
- `.10.4` same-input memo ON/OFF：1092 targets `check_exact=True`；full observer spectral 約 3.82 → 2.50 s。
- `.10.4 = FIELD PASS`。

## `.10.5` Targeted / actual-data gate

- Targeted Viewing/Glow chain：**23/23 PASS**。
- New route-group direct-reuse contract test：PASS。
- Actual TWS134 Glow 1092-target output：`check_dtype=True, check_exact=True` PASS。
- Actual TWS134 Main Viewing 585-target output：`check_dtype=True, check_exact=True` PASS。
- Glow local benchmark：約 2.50 → 2.01–2.19 s。
- Main Viewing local benchmark：約 1.50 → 1.24–1.33 s。

## Full regression

- Working tree：**670/670 PASS**
- Existing pandas FutureWarning：1（非 failure）
- Final FULL-CLEAN fresh-extract：**670/670 PASS**
- Existing pandas FutureWarning：1（同既有 warning，非 failure）
