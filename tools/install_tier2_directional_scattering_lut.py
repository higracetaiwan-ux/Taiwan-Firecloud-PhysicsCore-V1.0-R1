#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from firecloud.tier2_directional_scattering_runtime import install_directional_scattering_lut

p=argparse.ArgumentParser(description="驗證並安裝 R5.7.22 Full Directional Tier-2 雲散射 LUT。")
p.add_argument("csv")
p.add_argument("manifest")
p.add_argument("--runtime-dir", default=None)
a=p.parse_args()
audit=install_directional_scattering_lut(Path(a.csv).read_bytes(),Path(a.manifest).read_bytes(),a.runtime_dir)
print(json.dumps(audit,indent=2,ensure_ascii=False))
raise SystemExit(0 if audit.get("ok") else 2)
