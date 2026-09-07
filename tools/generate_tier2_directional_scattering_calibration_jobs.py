#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from firecloud.tier2_directional_scattering_calibration import build_directional_calibration_jobs

p=argparse.ArgumentParser(description="產生 R5.7.22 Full Directional Tier-2 外部 RT 校準工作表。")
p.add_argument("grid_spec_json")
p.add_argument("output_csv")
p.add_argument("--solver-family",required=True)
a=p.parse_args()
spec=json.loads(Path(a.grid_spec_json).read_text(encoding="utf-8"))
df=build_directional_calibration_jobs(spec,solver_family=a.solver_family)
Path(a.output_csv).parent.mkdir(parents=True,exist_ok=True)
df.to_csv(a.output_csv,index=False)
print(json.dumps({"ok":True,"rows":len(df),"output_csv":str(a.output_csv),"solver_family":a.solver_family},indent=2,ensure_ascii=False))
