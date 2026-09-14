#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd

from firecloud.ice_cloud_spectral_optics import read_tamu_isca_dat, normalize_tamu_isca_frame


def main() -> int:
    p=argparse.ArgumentParser(description="Build Firecloud six-band ice optics LUT rows from one TAMU ice isca.dat file")
    p.add_argument("--isca", required=True, help="Path to TAMU isca.dat")
    p.add_argument("--habit", required=True, help="Habit name, e.g. 8_columns")
    p.add_argument("--roughness", required=True, help="Rough000/Rough003/Rough050")
    p.add_argument("--output", required=True, help="Output CSV")
    p.add_argument("--source-version", default="Yang2013_Bi2017_V2")
    args=p.parse_args()
    raw=read_tamu_isca_dat(args.isca)
    out=normalize_tamu_isca_frame(raw, ice_habit=args.habit, surface_roughness=args.roughness, source_version=args.source_version)
    path=Path(args.output); path.parent.mkdir(parents=True,exist_ok=True)
    out.to_csv(path,index=False)
    print(f"wrote {len(out)} rows -> {path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
