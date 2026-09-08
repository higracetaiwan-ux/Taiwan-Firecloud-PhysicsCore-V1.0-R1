"""Detached event-analysis worker for Taiwan Firecloud PhysicsCore.

R5.7.23 Runtime Hardening adds an independent heartbeat/resource sampler and a
persistent stage trace.  The diagnostic layer is non-physical and cannot alter
Formation, Viewing, spectral RT, or cloud optics.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import pickle
import re
import sys
import threading
import time
import traceback

import pandas as pd

from .model import analyze_event
from .runtime_hardening import process_resource_snapshot, runtime_cache_mode, runtime_job_id


def _atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    os.replace(tmp, path)


def _atomic_pickle(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    with tmp.open("wb") as fh:
        pickle.dump(payload, fh, protocol=pickle.HIGHEST_PROTOCOL)
        fh.flush()
        try:
            os.fsync(fh.fileno())
        except Exception:
            pass
    os.replace(tmp, path)


def _atomic_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    pd.DataFrame(rows).to_csv(tmp, index=False)
    os.replace(tmp, path)


def _stage_identity(message: str) -> dict:
    text = str(message or "")
    m = re.search(r"太陽高度角\s*([+-]?\d+(?:\.\d+)?)°（(\d+)/(\d+)）[：:]?(.*)", text)
    if m:
        return {
            "solar_altitude_deg": float(m.group(1)),
            "angle_index": int(m.group(2)),
            "angle_count": int(m.group(3)),
            "stage": (m.group(4) or "").strip(" ：:") or "ANGLE_STAGE",
        }
    return {"solar_altitude_deg": None, "angle_index": None, "angle_count": None, "stage": text[:240]}


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 3:
        print("usage: python -m firecloud.analysis_worker REQUEST_JSON RESULT_PICKLE PROGRESS_JSON", file=sys.stderr)
        return 2

    request_path = Path(argv[0])
    result_path = Path(argv[1])
    progress_path = Path(argv[2])
    trace_path = progress_path.parent / "runtime_stage_trace.csv"
    resource_path = progress_path.parent / "runtime_resource_telemetry.csv"
    req = json.loads(request_path.read_text(encoding="utf-8"))
    started = datetime.now(timezone.utc)
    # R5.7.24.3: freeze provider-cycle availability against one immutable
    # analysis-start clock. Long CAMS/DWD waits must not let later per-angle
    # resolver calls jump to a newer GFS/CAMS cycle than the one prefetched at
    # the beginning of this same job. CAMS subprocesses inherit this value.
    os.environ["FIRECLOUD_PROVIDER_RESOLUTION_NOW_UTC"] = started.isoformat()
    started_mono = time.monotonic()
    job_id = runtime_job_id() or progress_path.parent.name
    run_mode = runtime_cache_mode()
    lock = threading.RLock()
    stop_event = threading.Event()
    trace_rows: list[dict] = []
    resource_rows: list[dict] = []
    current = {
        "message": "背景分析 worker 已啟動",
        "fraction": 0.0,
        "stage_started_mono": started_mono,
        "stage_seq": 0,
    }
    base = {
        "status": "RUNNING", "worker_pid": os.getpid(),
        "job_id": job_id, "analysis_run_mode": run_mode,
        "started_at_utc": started.isoformat(),
        "updated_at_utc": started.isoformat(), "progress_fraction": 0.0,
        "elapsed_seconds": 0.0, "exit_code": None,
        "last_message": current["message"], "error": "",
    }

    def _elapsed() -> float:
        return max(0.0, time.monotonic() - started_mono)

    def _append_trace(status: str, *, message: str | None = None, fraction: float | None = None) -> None:
        msg = str(current["message"] if message is None else message)
        ident = _stage_identity(msg)
        trace_rows.append({
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "job_id": job_id,
            "analysis_run_mode": run_mode,
            "stage_seq": int(current.get("stage_seq", 0)),
            "status": str(status),
            "progress_fraction": float(current["fraction"] if fraction is None else fraction),
            "elapsed_analysis_seconds": _elapsed(),
            "elapsed_stage_seconds": max(0.0, time.monotonic() - float(current.get("stage_started_mono", started_mono))),
            "last_message": msg,
            **ident,
        })

    def _append_resource(event: str) -> dict:
        snap = process_resource_snapshot()
        snap.update({
            "event": str(event),
            "progress_fraction": float(current.get("fraction", 0.0)),
            "last_message": str(current.get("message", "")),
            "elapsed_analysis_seconds": _elapsed(),
            "elapsed_stage_seconds": max(0.0, time.monotonic() - float(current.get("stage_started_mono", started_mono))),
            **_stage_identity(str(current.get("message", ""))),
        })
        resource_rows.append(snap)
        return snap

    def _persist_diag() -> None:
        try:
            _atomic_csv(trace_path, trace_rows)
        except Exception:
            pass
        try:
            _atomic_csv(resource_path, resource_rows)
        except Exception:
            pass

    def _progress_payload(status="RUNNING", error="", exit_code=None, resource=None) -> dict:
        payload = dict(base)
        payload.update({
            "status": status,
            "progress_fraction": float(current.get("fraction", 0.0)),
            "last_message": str(current.get("message", "")),
            "elapsed_seconds": _elapsed(),
            "stage_elapsed_seconds": max(0.0, time.monotonic() - float(current.get("stage_started_mono", started_mono))),
            "updated_at_utc": datetime.now(timezone.utc).isoformat(),
            "error": str(error or ""),
            "exit_code": exit_code,
            "runtime_stage_trace_path": str(trace_path),
            "runtime_resource_telemetry_path": str(resource_path),
        })
        if isinstance(resource, dict):
            for k in ("rss_mb", "peak_rss_mb", "vm_size_mb", "thread_count", "child_process_count"):
                payload[k] = resource.get(k)
        return payload

    with lock:
        _append_trace("STARTED")
        r0 = _append_resource("WORKER_START")
        _persist_diag()
        _atomic_json(progress_path, _progress_payload(resource=r0))

    def progress_callback(fraction: float, message: str) -> None:
        with lock:
            new_msg = str(message)
            new_frac = float(fraction)
            if new_msg != current["message"]:
                _append_trace("COMPLETED")
                current["message"] = new_msg
                current["fraction"] = new_frac
                current["stage_started_mono"] = time.monotonic()
                current["stage_seq"] = int(current.get("stage_seq", 0)) + 1
                _append_trace("STARTED")
            else:
                current["fraction"] = new_frac
                _append_trace("PROGRESS")
            resource = _append_resource("PROGRESS_CALLBACK")
            _persist_diag()
            _atomic_json(progress_path, _progress_payload(resource=resource))

    try:
        heartbeat_seconds = max(0.05, float(os.getenv("FIRECLOUD_RUNTIME_HEARTBEAT_SECONDS", "5")))
    except Exception:
        heartbeat_seconds = 5.0

    def heartbeat_loop() -> None:
        while not stop_event.wait(heartbeat_seconds):
            with lock:
                _append_trace("HEARTBEAT")
                resource = _append_resource("HEARTBEAT")
                _persist_diag()
                try:
                    _atomic_json(progress_path, _progress_payload(resource=resource))
                except Exception:
                    pass

    hb = threading.Thread(target=heartbeat_loop, name="firecloud-runtime-heartbeat", daemon=True)
    hb.start()

    try:
        day = req["day"]
        from datetime import date
        day_value = date.fromisoformat(str(day)) if not isinstance(day, date) else day
        result = analyze_event(
            float(req["lat"]), float(req["lon"]), day_value, str(req["event"]),
            req.get("tz_name") or None, progress_callback=progress_callback,
            timezone_mode=str(req.get("tz_mode", "AUTO_COORDINATE")),
        )
        stop_event.set(); hb.join(timeout=2.0)
        with lock:
            _append_trace("COMPLETED")
            _append_resource("WORKER_COMPLETED")
            _persist_diag()
            worker_trace_df = pd.DataFrame(trace_rows)
            worker_resource_df = pd.DataFrame(resource_rows)
        # Merge worker-level periodic telemetry with model-level DataFrame telemetry.
        model_resource = result.get("runtime_resource_telemetry", pd.DataFrame())
        if isinstance(model_resource, pd.DataFrame) and not model_resource.empty:
            result["runtime_resource_telemetry"] = pd.concat([worker_resource_df, model_resource], ignore_index=True, sort=False)
        else:
            result["runtime_resource_telemetry"] = worker_resource_df
        result["runtime_stage_trace"] = worker_trace_df
        result["runtime_execution_contract"] = pd.DataFrame([{
            "job_id": job_id,
            "analysis_run_mode": run_mode,
            "worker_pid": os.getpid(),
            "started_at_utc": started.isoformat(),
            "completed_at_utc": datetime.now(timezone.utc).isoformat(),
            "cold_cache_isolated": run_mode == "COLD_ISOLATED_TEST",
            "resume_same_job": run_mode == "RESUME_SAME_JOB",
            "provider_cache_reuse_allowed": run_mode != "COLD_ISOLATED_TEST",
            "provider_cycle_resolution_frozen": True,
            "provider_resolution_now_utc": os.getenv("FIRECLOUD_PROVIDER_RESOLUTION_NOW_UTC", started.isoformat()),
        }])
        _atomic_pickle(result_path, result)
        with lock:
            current["fraction"] = 1.0
            current["message"] = "背景分析完成"
            done_resource = _append_resource("RESULT_COMMITTED")
            _persist_diag()
            done = _progress_payload(status="COMPLETED", exit_code=0, resource=done_resource)
            done["progress_fraction"] = 1.0
            done["last_message"] = "背景分析完成"
            _atomic_json(progress_path, done)
        return 0
    except Exception as exc:
        stop_event.set(); hb.join(timeout=2.0)
        traceback_text = traceback.format_exc()[-12000:]
        error = f"{type(exc).__name__}: {exc}"
        print(traceback_text, file=sys.stderr, flush=True)
        with lock:
            _append_trace("FAILED")
            resource = _append_resource("WORKER_FAILED")
            _persist_diag()
            failed = _progress_payload(status="FAILED", error=error, exit_code=1, resource=resource)
            failed["last_message"] = error
            failed["traceback"] = traceback_text
            _atomic_json(progress_path, failed)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
