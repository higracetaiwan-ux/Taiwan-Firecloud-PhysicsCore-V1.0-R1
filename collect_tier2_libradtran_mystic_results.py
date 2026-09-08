from __future__ import annotations

import argparse
import json
from pathlib import Path
import pandas as pd

from firecloud.tier2_libradtran_mystic_adapter import (
    MYSTIC_ADAPTER_CONTRACT,
    parse_mc_rad_spc,
    parse_mc_rad_std_spc,
    external_result_row,
)
from firecloud.tier2_liquid_directional_calibration_pipeline import RESULT_CONTRACT, EXTERNAL_RESULT_REQUIRED_COLUMNS


def main() -> int:
    p = argparse.ArgumentParser(description="收集 genuine MYSTIC mc.rad.spc / mc.rad.std.spc 成為 R5.7.23 V3 external result table。")
    p.add_argument("--jobs-csv", required=True)
    p.add_argument("--run-dir", required=True)
    p.add_argument("--output-csv", required=True)
    p.add_argument("--solver-version", required=True)
    p.add_argument("--solver-run-prefix", default="MYSTIC-RUN")
    args = p.parse_args()

    jobs = pd.read_csv(args.jobs_csv)
    root = Path(args.run_dir)
    rows = []
    for i, job in enumerate(jobs.to_dict(orient="records"), 1):
        job_dir = root / str(job["job_id"])
        exec_path = job_dir / "job_execution.json"
        execution = json.loads(exec_path.read_text(encoding="utf-8")) if exec_path.exists() else {}
        exit_code = execution.get("solver_exit_code")
        rad = job_dir / "mc.rad.spc"
        std = job_dir / "mc.rad.std.spc"
        if exit_code == 0 and rad.exists() and std.exists():
            try:
                row = external_result_row(
                    job=job,
                    response_factor=parse_mc_rad_spc(rad),
                    response_factor_std=parse_mc_rad_std_spc(std),
                    solver_exit_code=0,
                    solver_version=args.solver_version,
                    solver_run_id=f"{args.solver_run_prefix}:{job['job_id']}",
                    result_contract=RESULT_CONTRACT,
                )
                response = float(row["response_factor"])
                stdv = float(row["response_factor_std"])
                row["sample_qc_state"] = "PASS"
                row["mc_relative_sigma"] = 0.0 if response == 0 and stdv == 0 else (float("inf") if response == 0 else stdv / response)
                rows.append(row)
                continue
            except Exception:
                pass
        rows.append({
            "job_id": str(job["job_id"]), "response_factor": None, "response_factor_std": None,
            "mc_absolute_sigma": None, "mc_relative_sigma": None, "photon_count": int(job.get("mc_photons", 0)),
            "sample_qc_state": "MISSING_OR_INVALID_MYSTIC_OUTPUT", "solver_run_id": f"{args.solver_run_prefix}:{job['job_id']}",
            "solver_exit_code": exit_code if exit_code is not None else -999,
            "solver_family": "LIBRADTRAN_UVSPEC_MYSTIC", "solver_version": args.solver_version,
            "result_contract": RESULT_CONTRACT, "adapter_contract": MYSTIC_ADAPTER_CONTRACT,
        })
    out = pd.DataFrame(rows, columns=EXTERNAL_RESULT_REQUIRED_COLUMNS)
    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output_csv, index=False)
    summary = {"row_count": int(len(out)), "pass_count": int(out["sample_qc_state"].eq("PASS").sum()), "adapter_contract": MYSTIC_ADAPTER_CONTRACT}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
