"""Detached event-analysis worker for Taiwan Firecloud PhysicsCore.

The Streamlit process must not own the lifetime of a long CAMS/RT analysis.
This module is launched with ``python -m firecloud.analysis_worker`` and writes
small JSON progress/checkpoint files plus one atomic result pickle.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import pickle
import sys
import traceback

from .model import analyze_event


def _atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    os.replace(tmp, path)


def _atomic_pickle(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("wb") as fh:
        pickle.dump(payload, fh, protocol=pickle.HIGHEST_PROTOCOL)
        fh.flush()
        try:
            os.fsync(fh.fileno())
        except Exception:
            pass
    os.replace(tmp, path)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 3:
        print("usage: python -m firecloud.analysis_worker REQUEST_JSON RESULT_PICKLE PROGRESS_JSON", file=sys.stderr)
        return 2

    request_path = Path(argv[0])
    result_path = Path(argv[1])
    progress_path = Path(argv[2])
    req = json.loads(request_path.read_text(encoding="utf-8"))
    started = datetime.now(timezone.utc)
    base = {
        "status": "RUNNING", "worker_pid": os.getpid(),
        "started_at_utc": started.isoformat(),
        "updated_at_utc": started.isoformat(), "progress_fraction": 0.0,
        "elapsed_seconds": 0.0, "exit_code": None,
        "last_message": "背景分析 worker 已啟動", "error": "",
    }
    _atomic_json(progress_path, base)

    def progress_callback(fraction: float, message: str) -> None:
        payload = dict(base)
        payload.update({
            "status": "RUNNING", "progress_fraction": float(fraction),
            "last_message": str(message),
            "elapsed_seconds": (datetime.now(timezone.utc) - started).total_seconds(),
            "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        })
        _atomic_json(progress_path, payload)

    try:
        day = req["day"]
        from datetime import date
        day_value = date.fromisoformat(str(day)) if not isinstance(day, date) else day
        result = analyze_event(
            float(req["lat"]), float(req["lon"]), day_value, str(req["event"]),
            str(req.get("tz_name", "Asia/Taipei")), progress_callback=progress_callback,
        )
        _atomic_pickle(result_path, result)
        done = dict(base)
        done.update({
            "status": "COMPLETED", "progress_fraction": 1.0,
            "last_message": "背景分析完成",
            "elapsed_seconds": (datetime.now(timezone.utc) - started).total_seconds(),
            "exit_code": 0,
            "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        })
        _atomic_json(progress_path, done)
        return 0
    except Exception as exc:
        traceback_text = traceback.format_exc()[-12000:]
        error = f"{type(exc).__name__}: {exc}"
        print(traceback_text, file=sys.stderr, flush=True)
        failed = dict(base)
        failed.update({
            "status": "FAILED", "last_message": error, "error": error,
            "traceback": traceback_text,
            "elapsed_seconds": (datetime.now(timezone.utc) - started).total_seconds(),
            "exit_code": 1,
            "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        })
        _atomic_json(progress_path, failed)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
