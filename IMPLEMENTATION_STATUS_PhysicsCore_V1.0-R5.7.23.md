# Taiwan Firecloud PhysicsCore V1.0-R5.7.23 實作狀態

## 正式基線

來源：**V1.0-R5.7.22.1 ACCEPTED BASELINE**。

R5.7.23 不重新定義既有 PhysicsCore 權重或 Formation / Viewing 科學狀態。

## 已完成

- [x] REAL Tier-2-ready liquid calibration target selector
- [x] COT / r_eff / θ₀ / θᵥ / Δφ 真實 domain planner
- [x] 六波段 full-directional job grid
- [x] libRadtran/MYSTIC spherical solver recipe
- [x] uvspec input template
- [x] Cloud→Observer θᵥ 到 uvspec `umu` adapter
- [x] external result required schema
- [x] job completeness / duplicate / unknown-job QC
- [x] response / Monte-Carlo convergence / exit-code QC
- [x] solver family / version provenance QC
- [x] external genuine result → R5.7.22 production LUT package builder
- [x] runtime LUT bytes + manifest validation
- [x] CLI job generator
- [x] CLI production package builder
- [x] R5.7.23 regression tests

## 本環境限制

建置環境目前沒有 `uvspec` 執行檔，因此無法在本次封裝內聲稱已完成 genuine libRadtran/MYSTIC calibration run。

因此：

- Production calibrated LUT：**尚未生成**
- Production LUT install：**尚未執行**
- Tier-2 production solver：應繼續在沒有 genuine LUT 時保持 blocked

這不是錯誤回退，而是刻意維持 calibration provenance 與 Missing 語義。

## 下一個實際驗收

1. 以 REAL R5.7.22.1 CASE 的 Tier-2 foundation / readiness CSV 產生 calibration bundle。
2. 在具有 genuine libRadtran/MYSTIC spherical 環境執行所有 jobs。
3. 收集六波段 response 與 Monte-Carlo uncertainty。
4. 通過 R5.7.23 external-result QC。
5. 建立並安裝 production directional LUT。
6. 重新跑同一 REAL_CANVAS CASE，確認 `INPUTS_READY_AWAITING_LUT_SOLVER` 進入 deterministic interpolation。

## 後續但非本版範圍

- GFS 09Z / 10Z temporal interpolation contract
- ice-cloud genuine directional LUT
- cloud thickness sensitivity study
- calibration atmosphere / liquid droplet effective variance / normalization protocol 最終定案
