# Taiwan Firecloud PhysicsCore V1.0-R5.7.28 Release Notes

## 主旨

**Red-Light Evidence Robustness**

## Field CASE forensic

R5.7.27.1 真實部署 CASE 已完成驗收：Photography Decision 13/13 angles、
Formation hard NO-GO dominance、Analysis Integrity overall 與 CASE archive
member checks 全部 PASS。唯一 WARN 為 CAMS spectral AOD payload 2/13：09Z
request 在 90 秒 deadline timeout，12Z 成功。

## 修正

- 新增真實 CAMS adjacent-time spectral AOD 支援，硬限制 3 小時。
- 只依 `point_id` 搬移 550／645／670／800 nm 原生欄位。
- O3、原生 3D aerosol、cloud、gas 與 geometry 保持 exact-time。
- 新增 row-level source valid time、time offset、bound 與 temporal state。
- Red-Light cloud／aerosol／gas／precipitation evidence 分欄輸出。
- Analysis Integrity 新增 temporal provenance 與 component separation checks。

## 不變

- 13 angles、六波段與 full route invariance 不變。
- Formation、Viewing、Glow 永久分離。
- Missing ≠ Clear ≠ Zero ≠ N/A。
- 不使用固定 Angstrom、固定 O3 或人工 aerosol。
- R5.7.27.1 Photography Integrity handoff／CASE guard 完整保留。

## 驗證

- R5.7.28 專項與相鄰契約：41 passed / 0 failed。
- Working tree 完整 regression：467 passed / 0 failed。
- FULL-CLEAN 解壓 regression：467 passed / 0 failed。
