#!/usr/bin/env python3
"""Fast offline semantic replay for R5.7.41 Canvas Vertical Microphysics Overlap.

This tool reads an existing R5.7.40/R5.7.40.1 CASE ZIP (or extracted CASE
directory) and reclassifies the already-exported vertical-conflict evidence into
R5.7.41 boundary-vs-interior semantics. It does NOT call GFS/CAMS and does NOT
replace the production R5.7.41 overlap engine. It is intended as a fast regression
fixture before one final online CASE run.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import tempfile
import zipfile

import numpy as np
import pandas as pd

THRESHOLD = 1.0e-7
REPLAY_CONTRACT = (
    "R5.7.41_OFFLINE_REPLAY_FROM_R5.7.40_QUALIFICATION;"
    "NO_NETWORK;NO_COT_PROMOTION;NO_FORMATION_PROMOTION;NOT_PRODUCTION_OVERLAP_OUTPUT"
)


def _load_case(path: Path) -> pd.DataFrame:
    if path.is_dir():
        p = path / "v1_canvas_vertical_conflict_qualification.csv"
        if not p.exists():
            raise FileNotFoundError(p)
        return pd.read_csv(p)
    if path.suffix.lower() != ".zip":
        raise ValueError("CASE input must be a CASE ZIP or extracted CASE directory")
    with zipfile.ZipFile(path, "r") as zf:
        names = [n for n in zf.namelist() if n.endswith("v1_canvas_vertical_conflict_qualification.csv")]
        if not names:
            raise FileNotFoundError("v1_canvas_vertical_conflict_qualification.csv not found in CASE ZIP")
        with zf.open(names[0]) as fh:
            return pd.read_csv(fh)


def _finite(v):
    try:
        return bool(np.isfinite(float(v)))
    except Exception:
        return False


def _position(z, z0, z1, tol=1e-8):
    if not _finite(z):
        return "UNKNOWN"
    z=float(z); z0=float(z0); z1=float(z1)
    if abs(z-z0) <= tol: return "BOUNDARY_LOWER"
    if abs(z-z1) <= tol: return "BOUNDARY_UPPER"
    if z0 < z < z1: return "INTERIOR"
    if z < z0: return "BELOW_TARGET"
    if z > z1: return "ABOVE_TARGET"
    return "BOUNDARY_NEAR"


def replay(df: pd.DataFrame) -> pd.DataFrame:
    required = {
        "time","solar_altitude_deg","canvas_id","target_z_base_km","target_z_top_km",
        "primary_neighbor_context_complete","supplement_hydrometeor_bracket_complete",
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"CASE qualification schema missing: {missing}")
    rows=[]
    for _,r in df.iterrows():
        z0,z1=float(r.target_z_base_km),float(r.target_z_top_km)
        samples=[]
        for prefix, role in [
            ("below_primary","PRIMARY_NEIGHBOR"), ("above_primary","PRIMARY_NEIGHBOR"),
            ("below_supplement","PGRB2B_INTERMEDIATE"), ("above_supplement","PGRB2B_INTERMEDIATE"),
        ]:
            z=r.get(f"{prefix}_altitude_agl_km", np.nan)
            q=r.get(f"{prefix}_total_condensate_kgkg", np.nan)
            st=str(r.get(f"{prefix}_condensate_state", ""))
            if not _finite(z):
                continue
            positive = st == "POSITIVE" or (_finite(q) and float(q) >= THRESHOLD)
            samples.append((_position(z,z0,z1), positive, st, z, q, role))
        interior_positive = any(pos and posn == "INTERIOR" for posn,pos,*_ in samples)
        boundary_positive = any(pos and posn.startswith("BOUNDARY") for posn,pos,*_ in samples)
        complete = bool(r.primary_neighbor_context_complete) and bool(r.supplement_hydrometeor_bracket_complete)
        if not complete:
            state="VERTICAL_EVIDENCE_INCOMPLETE"
        elif interior_positive:
            state="MIXED_CONFLICT_WITH_INTERIOR_SUPPORT"
        elif boundary_positive:
            state="BOUNDARY_ONLY_NATIVE_CONDENSATE_SUPPORT"
        else:
            state="NO_NATIVE_CONDENSATE_SUPPORT"
        rows.append({
            "time":r.time, "solar_altitude_deg":r.solar_altitude_deg, "canvas_id":r.canvas_id,
            "target_z_base_km":z0, "target_z_top_km":z1,
            "legacy_vertical_conflict_qualification":r.get("vertical_conflict_qualification"),
            "r5741_replay_overlap_state":state,
            "replay_interior_positive":bool(interior_positive),
            "replay_boundary_positive":bool(boundary_positive),
            "cot_promotion_allowed":False, "formation_promotion_allowed":False,
            "replay_contract":REPLAY_CONTRACT,
        })
    return pd.DataFrame(rows)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("case", type=Path, help="R5.7.40/R5.7.40.1 CASE ZIP or extracted CASE directory")
    ap.add_argument("--output", type=Path, default=None, help="optional replay CSV output path")
    args=ap.parse_args()
    src=_load_case(args.case)
    out=replay(src)
    print(f"rows={len(out)}; unique_canvases={out.canvas_id.astype(str).nunique()}")
    print(out.r5741_replay_overlap_state.value_counts(dropna=False).to_string())
    cross=pd.crosstab(out.legacy_vertical_conflict_qualification,out.r5741_replay_overlap_state)
    print("\nlegacy -> R5.7.41 replay")
    print(cross.to_string())
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        out.to_csv(args.output,index=False)
        print(f"\nwritten: {args.output}")

if __name__ == "__main__":
    main()
