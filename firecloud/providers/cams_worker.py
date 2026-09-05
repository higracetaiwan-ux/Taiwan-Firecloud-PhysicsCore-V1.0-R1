"""Minimal external CAMS role worker for Taiwan Firecloud V8.4.10.5.

This module is launched with ``python -m firecloud.providers.cams_worker`` so the
worker imports the provider stack only; it never reconstructs Streamlit app.py.
"""
from __future__ import annotations

from datetime import datetime
import json
import pickle
from pathlib import Path
import sys

from .cams_native import _cams_role_worker


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print("usage: python -m firecloud.providers.cams_worker REQUEST_JSON RESULT_PICKLE", file=sys.stderr)
        return 2
    request_path = Path(argv[0])
    result_path = Path(argv[1])
    req = json.loads(request_path.read_text(encoding="utf-8"))
    valid_time = datetime.fromisoformat(req["valid_time"])
    _cams_role_worker(
        str(result_path),
        str(req["role"]),
        list(req["points"]),
        valid_time,
        req.get("cache_dir"),
    )
    if not result_path.exists() or result_path.stat().st_size <= 0:
        return 1
    try:
        with result_path.open("rb") as fh:
            result = pickle.load(fh)
        status = str(result.get("status", "FAILED")).upper() if isinstance(result, dict) else "FAILED"
        return 0 if status in {"OK", "CACHE_HIT"} else 1
    except Exception:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
