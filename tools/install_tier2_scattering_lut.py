#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from firecloud.tier2_scattering_runtime import install_scattering_lut

p=argparse.ArgumentParser(description="Validate and install a calibrated Taiwan Firecloud Tier-2 scattering LUT.")
p.add_argument("csv")
p.add_argument("manifest")
p.add_argument("--runtime-dir", default=None)
a=p.parse_args()
audit=install_scattering_lut(Path(a.csv).read_bytes(), Path(a.manifest).read_bytes(), a.runtime_dir)
print(json.dumps(audit, indent=2, ensure_ascii=False))
raise SystemExit(0 if audit.get("ok") else 2)
