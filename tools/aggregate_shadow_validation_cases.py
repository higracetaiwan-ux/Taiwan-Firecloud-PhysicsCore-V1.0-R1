#!/usr/bin/env python3
"""Aggregate R5.7.41.3 Shadow Validation CASE summaries offline.

Usage:
  python tools/aggregate_shadow_validation_cases.py CASE1.zip CASE2.zip ... -o shadow_validation_cohort.csv

The tool reads only CASE CSV artifacts and never calls providers.
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path
import zipfile
import pandas as pd

SUMMARY_MEMBER = "shadow_validation_cohort_summary.csv"
MANIFEST_MEMBER = "shadow_validation_case_manifest.csv"


def _read_member(zf: zipfile.ZipFile, name: str) -> pd.DataFrame:
    if name not in zf.namelist():
        return pd.DataFrame()
    return pd.read_csv(io.BytesIO(zf.read(name)))


def aggregate_case_archives(paths: list[str | Path]) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for raw in paths:
        path = Path(raw)
        with zipfile.ZipFile(path, "r") as zf:
            summary = _read_member(zf, SUMMARY_MEMBER)
            if summary.empty:
                manifest = _read_member(zf, MANIFEST_MEMBER)
                if manifest.empty:
                    continue
                summary = manifest.copy()
            summary = summary.copy()
            summary["case_archive_filename"] = path.name
            rows.append(summary)
    if not rows:
        return pd.DataFrame()
    out = pd.concat(rows, ignore_index=True, sort=False)
    sort_cols = [c for c in ("event_date", "event", "site_id", "shadow_validation_case_id") if c in out.columns]
    if sort_cols:
        out = out.sort_values(sort_cols, kind="stable").reset_index(drop=True)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cases", nargs="+")
    ap.add_argument("-o", "--output", default="shadow_validation_cohort.csv")
    args = ap.parse_args()
    out = aggregate_case_archives(args.cases)
    if out.empty:
        raise SystemExit("No R5.7.41.3 Shadow Validation collection artifacts found.")
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False)
    print(f"WROTE {args.output} rows={len(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
