# Yang/Bi V2 Authoritative Ice Source Acquisition Guide

## Required file

`Data_0.2_15.25.tar.gz`

Expected MD5:

`2fb9bbab2c2c735a869c863a680e2f70`

Source record:

`Zenodo 5348402`

The file is large (~27.4 GB). Do not include it inside PhysicsCore or WINDY release ZIPs.

## Workflow

1. Download the published archive from the source record.
2. Verify MD5 before scientific use.
3. Extract to a dedicated source-data directory.
4. Preserve the original directory names for all habits/roughness states.
5. Run `tools/build_authoritative_ice_optics_lut.py` with both `--archive` and `--source-root`.
6. Do not manually edit any `isca.dat` values.
7. Preserve the resulting source inventory, spectral audit and QA JSON alongside the released LUT.

## Why the archive checksum is a release gate

A structurally complete extracted directory is not enough to establish published-source identity. A calibrated portable package is only released when the published archive checksum has also been verified.

## Windows helper

`tools/prepare_tamu_ice_v2_source.ps1` performs MD5 verification, extraction, authoritative QA/LUT build, and portable-package emission. It does not download the archive automatically.
