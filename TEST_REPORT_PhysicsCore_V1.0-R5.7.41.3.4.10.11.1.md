# Test Report — V1.0-R5.7.41.3.4.10.11.1

## Scope

TAMU V2 source contract correction, Dmax-first authoritative LUT and WINDY portable V1.1.

## Working-tree regression

- `pytest -q`
- **761/761 PASS**
- 1 existing pandas `FutureWarning`
- 0 failures

## Targeted Ice / portable tests

- authoritative source manifest / checksum contract
- `hollow_column` alias resolution
- missing-source fail-close
- wavelength-dependent source geometry acceptance
- Dmax-first six-band group completeness
- no spectral extrapolation
- portable Dmax exact lookup / interpolation
- positive-IWP no-Dmax fail-close
- Node evaluator parity
- TypeScript strict compile
- UI information architecture / runtime decoupling

Targeted aggregate used for current gate: **28/28 PASS**.

## Real Yang/Bi source samples supplied by user

### HBR Rough000

- rows: 74844
- wavelengths: 396
- sizes: 189
- source QA: PASS
- max volume relative spread across wavelength: ~1.5983
- projected-area spread: 0
- target bands: 6/6 PASS

### SBR Rough000

- rows: 74844
- wavelengths: 396
- sizes: 189
- source QA: PASS
- max volume relative spread across wavelength: ~1.1123
- projected-area spread: 0
- target bands: 6/6 PASS

### HBR normalized portable smoke test

- six-band LUT rows: 1134 = 189×6
- Dmax groups: 189
- bands: 550/575/600/650/700/750
- Node `validation/validatePackage.mjs`: **PASS 6 vectors**

## Full 27-source external gate

尚待使用者本機以完整 extracted source 重跑 `.10.11.1` builder；本報告不宣稱 27/27 已在此環境重新 PASS。

## Frozen science audit

Compared with `.10.11` certified baseline:

- **16/16 frozen science source files byte-identical**
- no Formation / Viewing / Glow / Red-Light / COT frozen file changed

See `FROZEN_SCIENCE_SOURCE_AUDIT_R5.7.41.3.4.10.11.1.csv`.

## Fresh-extract regression

Preliminary FULL-CLEAN fresh extract：

- **761/761 PASS**
- 1 existing pandas `FutureWarning`
- 0 failures

Final release package rebuilt after this report update.

Final FULL-CLEAN fresh extract verification：**761/761 PASS**；同一個既有 pandas `FutureWarning`，0 failures。
