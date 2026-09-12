# CASE Export Buffered ZIP Streaming Spec — R5.7.41.3.4.6

## 1. Scope

本文件是 R5.7.41.3.4.6 Runtime / I-O Hardening 的 CASE-export 子規格；完整版本另包含 DWD persistent raw cache、API audit correction 與 aggregation profiling。CASE export 子項只最佳化 CSV serialization I/O。Science baseline 保持：

`R5.7.41.2_SHADOW_COT_AB_FROZEN`

不修改任何 Forecast / Shadow / Formation / Viewing / Twilight Glow / Photography evidence。

## 2. Existing contract

CASE generation 維持 R2.1 的基本原則：

- 只有使用者按下「產生 CASE ZIP」才序列化；
- DataFrame 直接串流寫入 `ZipExtFile`；
- 不建立整份 CSV 的巨大 intermediate string/bytes；
- ZIP 使用 `ZIP_DEFLATED`, `compresslevel=1`；
- `case_archive_manifest.csv` 保存每個 CSV **uncompressed payload** 的 row count、byte size 與 SHA256。

## 3. Bottleneck

`pandas.DataFrame.to_csv()` 會對 text writer 發出大量較小的 `write(str)` 呼叫。舊 writer 每次都：

1. UTF-8 encode；
2. 更新 SHA256；
3. 立即 `ZipExtFile.write()`；
4. 直接進入 zlib stream。

大型 voxel / microphysics CSV 可達數十 MB，因此 Python → ZipExtFile → zlib 的大量小 write call 形成可避免的 overhead。

## 4. R5.7.41.3.4.6 design

新增 `firecloud.case_archive_stream`：

- `_BufferedHashingTextWriter`
- `write_dataframe_csv_member()`

Writer 行為：

- 每次輸入仍立即用完全相同 UTF-8 bytes 更新 SHA256 與 byte count；
- bytes 暫存在有界 `bytearray`；
- 預設最多 **4 MiB** 後 flush 到 `ZipExtFile`；
- 單一 write 若大於 buffer threshold，先 flush 現有 buffer，再直接寫入該 payload；
- member 結束前強制 flush；
- 不 materialize 整份 CSV。

## 5. Compatibility constraints

必須保持：

- CSV bytes exact-equivalent；
- SHA256 exact-equivalent；
- byte_size exact-equivalent；
- row_count exact-equivalent；
- ZIP compression method/level 不變；
- `case_archive_manifest.csv` schema 不增加 buffering-only columns；
- CASE Integrity 第二層稽核不變。

## 6. Telemetry

`CASE_EXPORT_SERIALIZATION` 與 `TOTAL_TO_CASE_ARCHIVE` 的 `cache_status` 更新為：

`COMPUTED_STREAMING_BUFFERED_4MIB`

此欄僅表達工程路徑，不代表 physics/cache result。

## 7. Benchmark

使用 H004 / TWS021 保存 CASE 中三個最大代表性 CSV，DataFrame 已先載入，計時只包含 DataFrame→CSV→ZIP serialization：

- `native_cloud_optical_blocking_voxel_3d.csv`：3.656 s → 3.475 s
- `optical_blocking_voxel_3d.csv`：1.922 s → 1.724 s
- `v1_canvas_vertical_microphysics_samples.csv`：1.189 s → 1.069 s

合計：

- legacy：6.766 s
- buffered：6.268 s
- reduction：約 **7.36%**
- speedup：約 **1.079×**

三檔：

- uncompressed SHA256：exact match
- uncompressed byte size：exact match
- compressed ZIP member size：exact match

這是代表性大型 CSV benchmark，不宣稱 full CASE 一定固定快 7.36%；實際收益依 DataFrame 欄位型態、CPU、zlib 與部署環境而變。
