#!/usr/bin/env python
"""Offline R5.7.41.1 COT diagnostic reconciliation replay.

Usage:
  python tools/replay_r57411_cot_reconciliation.py CASE.zip --out replay_out
  python tools/replay_r57411_cot_reconciliation.py CASE_DIR --out replay_out

No network access is used.
"""
from __future__ import annotations

import argparse
import tempfile
import zipfile
from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from firecloud.canvas_cot_reconciliation import (
    build_canvas_cot_reconciliation,
    summarize_canvas_cot_reconciliation,
)

REQ = [
    "v1_target_canvas_optical_evidence.csv",
    "v1_canvas_vertical_microphysics_overlap.csv",
    "v1_canvas_vertical_microphysics_samples.csv",
]


def _resolve_case(path: Path, tmp: Path) -> Path:
    if path.is_dir():
        return path
    if path.suffix.lower() != ".zip":
        raise SystemExit("CASE must be a directory or .zip")
    with zipfile.ZipFile(path) as zf:
        zf.extractall(tmp)
    return tmp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case")
    ap.add_argument("--out", default="r57411_cot_reconciliation_replay")
    args = ap.parse_args()
    case = Path(args.case).resolve()
    out = Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="r57411_") as td:
        root = _resolve_case(case, Path(td))
        missing = [n for n in REQ if not (root / n).exists()]
        if missing:
            raise SystemExit("Missing CASE evidence: " + ", ".join(missing))
        target = pd.read_csv(root / REQ[0])
        overlap = pd.read_csv(root / REQ[1])
        samples = pd.read_csv(root / REQ[2])
        rec = build_canvas_cot_reconciliation(target, overlap, samples)
        summary = summarize_canvas_cot_reconciliation(rec)
        rec.to_csv(out / "v1_canvas_cot_reconciliation.csv", index=False)
        summary.to_csv(out / "v1_canvas_cot_reconciliation_summary.csv", index=False)
        print(f"rows={len(rec)}")
        if rec.empty:
            print("state=NO_COMPARABLE_EXACT_COT_PAIR")
        else:
            print(rec["reconciliation_state"].value_counts(dropna=False).to_string())
            residual = pd.to_numeric(rec["reconciliation_residual_cot"], errors="coerce")
            print(f"max_abs_residual={residual.abs().max():.12g}")
            print(f"legacy_reconstruction_matches={int(rec['legacy_reconstruction_matches'].fillna(False).astype(bool).sum())}/{len(rec)}")
            print(f"production_target_cot_replaced={int(rec['production_target_cot_replaced'].fillna(False).astype(bool).sum())}")
        print(f"output={out}")


if __name__ == "__main__":
    main()
