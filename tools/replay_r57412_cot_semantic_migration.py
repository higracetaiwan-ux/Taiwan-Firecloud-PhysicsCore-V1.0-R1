#!/usr/bin/env python
"""Offline R5.7.41.2 Production COT semantic migration shadow replay.

Usage:
  python tools/replay_r57412_cot_semantic_migration.py CASE.zip --out replay_out
  python tools/replay_r57412_cot_semantic_migration.py CASE_DIR --out replay_out

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

from firecloud.canvas_cot_semantic_migration import (
    build_canvas_cot_semantic_migration_shadow,
    summarize_canvas_cot_semantic_migration_shadow,
)

REQ = [
    "v1_target_canvas_optical_evidence.csv",
    "v1_canvas_vertical_microphysics_overlap.csv",
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
    ap.add_argument("--out", default="r57412_cot_semantic_migration_replay")
    args = ap.parse_args()
    case = Path(args.case).resolve()
    out = Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="r57412_") as td:
        root = _resolve_case(case, Path(td))
        missing = [n for n in REQ if not (root / n).exists()]
        if missing:
            raise SystemExit("Missing CASE evidence: " + ", ".join(missing))
        target = pd.read_csv(root / REQ[0])
        overlap = pd.read_csv(root / REQ[1])
        shadow = build_canvas_cot_semantic_migration_shadow(target, overlap)
        summary = summarize_canvas_cot_semantic_migration_shadow(shadow)
        shadow.to_csv(out / "v1_canvas_cot_semantic_migration.csv", index=False)
        summary.to_csv(out / "v1_canvas_cot_semantic_migration_summary.csv", index=False)
        print(f"rows={len(shadow)}")
        if not shadow.empty:
            eligible = shadow["shadow_candidate_eligible"].fillna(False).astype(bool)
            print(f"eligible={int(eligible.sum())}")
            print(f"ineligible={int((~eligible).sum())}")
            print("ineligibility_reasons:")
            print(shadow.loc[~eligible, "migration_ineligibility_reasons"].value_counts(dropna=False).to_string())
            print(f"production_switch_performed={int(shadow['production_switch_performed'].fillna(False).astype(bool).sum())}")
            print(f"cot_promotion_allowed={int(shadow['cot_promotion_allowed'].fillna(False).astype(bool).sum())}")
            print(f"formation_promotion_allowed={int(shadow['formation_promotion_allowed'].fillna(False).astype(bool).sum())}")
        print(f"output={out}")


if __name__ == "__main__":
    main()
