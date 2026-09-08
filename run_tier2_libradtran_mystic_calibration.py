from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
from datetime import datetime, timezone

import pandas as pd

from firecloud.tier2_libradtran_mystic_adapter import (
    MYSTIC_ADAPTER_CONTRACT,
    unit_solar_spectrum_text,
    liquid_cloud_profile_text,
    render_uvspec_input,
)
from firecloud.runtime_hardening import atomic_write_text


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def render_job(job: dict, *, run_root: Path, recipe: dict, data_files_path: str, atmosphere_file: str) -> Path:
    job_id = str(job["job_id"])
    job_dir = run_root / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    solar = job_dir / "unit_solar_spectrum.dat"
    cloud = job_dir / "liquid_cloud.dat"
    inp = job_dir / "uvspec.inp"
    atomic_write_text(solar, unit_solar_spectrum_text())
    atomic_write_text(
        cloud,
        liquid_cloud_profile_text(
            cloud_base_km=float(recipe["reference_cloud_base_km"]),
            cloud_top_km=float(recipe["reference_cloud_top_km"]),
            effective_radius_um=float(job["effective_radius_um"]),
        ),
    )
    text = render_uvspec_input(
        job,
        data_files_path=data_files_path,
        atmosphere_file=atmosphere_file,
        solar_spectrum_file=solar.name,
        cloud_profile_file=cloud.name,
        sensor_altitude_km=float(recipe["reference_cloud_base_km"]),
    )
    atomic_write_text(inp, text)
    return job_dir


def main() -> int:
    p = argparse.ArgumentParser(description="R5.7.23 genuine libRadtran/MYSTIC batch runner；無 uvspec 時只允許 render-only。")
    p.add_argument("--jobs-csv", required=True)
    p.add_argument("--solver-recipe-json", required=True)
    p.add_argument("--run-dir", required=True)
    p.add_argument("--data-files-path", default=os.environ.get("LIBRADTRAN_DATA_FILES_PATH", ""))
    p.add_argument("--atmosphere-file", default=os.environ.get("LIBRADTRAN_ATMOSPHERE_FILE", ""))
    p.add_argument("--uvspec", default="")
    p.add_argument("--timeout-seconds", type=int, default=7200)
    p.add_argument("--max-jobs", type=int, default=0)
    p.add_argument("--render-only", action="store_true")
    args = p.parse_args()

    jobs = pd.read_csv(args.jobs_csv)
    recipe = json.loads(Path(args.solver_recipe_json).read_text(encoding="utf-8"))
    if str(recipe.get("solver_adapter_contract", "")) != MYSTIC_ADAPTER_CONTRACT:
        raise RuntimeError("MYSTIC_ADAPTER_CONTRACT_MISMATCH")
    if not args.data_files_path or not args.atmosphere_file:
        raise RuntimeError("LIBRADTRAN_DATA_PATH_AND_ATMOSPHERE_REQUIRED")
    selected = jobs.head(args.max_jobs) if args.max_jobs > 0 else jobs
    run_root = Path(args.run_dir)
    run_root.mkdir(parents=True, exist_ok=True)

    exe = args.uvspec or shutil.which("uvspec") or ""
    if not args.render_only and not exe:
        raise RuntimeError("UVSPEC_NOT_FOUND_EXTERNAL_RUNTIME_REQUIRED")

    audit_rows = []
    for row in selected.to_dict(orient="records"):
        job_dir = render_job(row, run_root=run_root, recipe=recipe, data_files_path=args.data_files_path, atmosphere_file=args.atmosphere_file)
        state = "RENDERED_NOT_EXECUTED"
        exit_code = None
        started = _utc()
        finished = started
        stderr_tail = ""
        if not args.render_only:
            inp = (job_dir / "uvspec.inp").read_text(encoding="utf-8")
            proc = subprocess.run(
                [exe], input=inp, text=True, cwd=job_dir,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=max(1, int(args.timeout_seconds)), check=False,
            )
            (job_dir / "uvspec.stdout.log").write_text(proc.stdout or "", encoding="utf-8")
            (job_dir / "uvspec.stderr.log").write_text(proc.stderr or "", encoding="utf-8")
            exit_code = int(proc.returncode)
            state = "EXECUTED_OK" if exit_code == 0 else "EXECUTED_FAILED"
            stderr_tail = (proc.stderr or "")[-2000:]
            finished = _utc()
        execution = {
            "job_id": str(row["job_id"]), "state": state, "solver_exit_code": exit_code,
            "solver_executable": exe if exe else None, "started_at_utc": started,
            "finished_at_utc": finished, "adapter_contract": MYSTIC_ADAPTER_CONTRACT,
            "stderr_tail": stderr_tail,
        }
        atomic_write_text(job_dir / "job_execution.json", json.dumps(execution, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        audit_rows.append(execution)
    pd.DataFrame(audit_rows).to_csv(run_root / "mystic_batch_execution_audit.csv", index=False)
    summary = {
        "state": "RENDER_ONLY_EXTERNAL_SOLVER_PENDING" if args.render_only else "BATCH_EXECUTION_COMPLETE",
        "job_count": len(audit_rows), "render_only": bool(args.render_only),
        "uvspec_found": bool(exe), "adapter_contract": MYSTIC_ADAPTER_CONTRACT,
    }
    atomic_write_text(run_root / "mystic_batch_execution_summary.json", json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
