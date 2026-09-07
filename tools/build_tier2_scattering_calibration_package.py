#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd
from firecloud.tier2_scattering_calibration import build_calibration_package

p=argparse.ArgumentParser(description="Build a production-gated Tier-2 scattering LUT CSV + manifest from externally calibrated RT samples.")
p.add_argument("samples_csv")
p.add_argument("metadata_json")
p.add_argument("output_dir")
a=p.parse_args()
samples=pd.read_csv(a.samples_csv)
meta=json.loads(Path(a.metadata_json).read_text(encoding="utf-8"))
csv_bytes,manifest_bytes,audit=build_calibration_package(samples,meta)
out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True)
(out/"tier2_scattering_lut.csv").write_bytes(csv_bytes)
(out/"tier2_scattering_lut_manifest.json").write_bytes(manifest_bytes)
print(json.dumps({**audit,"output_dir":str(out)},indent=2,ensure_ascii=False))
