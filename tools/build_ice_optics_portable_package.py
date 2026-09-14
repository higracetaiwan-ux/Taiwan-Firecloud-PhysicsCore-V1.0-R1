from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import firecloud
from firecloud.ice_cloud_spectral_optics import IceOpticsLUTStatus, validate_ice_optics_lut
from firecloud.ice_optics_portable import write_portable_package


def main() -> int:
    ap = argparse.ArgumentParser(description="Build standalone Firecloud Ice Optics package for WINDY; no PhysicsCore runtime dependency.")
    ap.add_argument("--lut", required=True, help="Validated six-band ice_optics_lut_v1.csv")
    ap.add_argument("--output", required=True, help="Output .zip path")
    ap.add_argument("--science-baseline", default="R5.7.41.2_SHADOW_COT_AB_FROZEN")
    ap.add_argument("--source-manifest", default=str(ROOT / "firecloud" / "data" / "ice_optics_source_manifest_v1.json"))
    args = ap.parse_args()

    lut_path = Path(args.lut).expanduser().resolve()
    lut = validate_ice_optics_lut(pd.read_csv(lut_path), require_full_six_band=True)
    if lut.empty:
        raise SystemExit("Refusing to build a portable WINDY package from an empty LUT")
    source = None
    src = Path(args.source_manifest).expanduser()
    if src.exists():
        source = json.loads(src.read_text(encoding="utf-8"))
    status = IceOpticsLUTStatus(True, str(lut_path), len(lut), True, "ICE_OPTICS_LUT_READY")
    out = write_portable_package(
        args.output,
        lut,
        physicscore_version=firecloud.__version__,
        science_baseline=args.science_baseline,
        lut_status=status,
        source_manifest=source,
    )
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
