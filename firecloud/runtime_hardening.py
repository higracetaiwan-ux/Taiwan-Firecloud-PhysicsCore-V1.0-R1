"""R5.7.23 runtime hardening utilities.

This module is deliberately non-physical.  It provides cache provenance,
atomic cache commits, run-mode identity, and lightweight process telemetry.
It must never alter Formation, Viewing, cloud optics, or spectral results.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import resource
import tempfile
import uuid

CACHE_MODE_WARM = "WARM_PRODUCTION"
CACHE_MODE_COLD = "COLD_ISOLATED_TEST"
CACHE_MODE_RESUME = "RESUME_SAME_JOB"
VALID_CACHE_MODES = {CACHE_MODE_WARM, CACHE_MODE_COLD, CACHE_MODE_RESUME}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def runtime_job_id() -> str:
    return str(os.getenv("FIRECLOUD_JOB_ID", "") or "").strip()


def runtime_cache_mode() -> str:
    mode = str(os.getenv("FIRECLOUD_ANALYSIS_RUN_MODE", CACHE_MODE_WARM) or CACHE_MODE_WARM).strip().upper()
    return mode if mode in VALID_CACHE_MODES else CACHE_MODE_WARM


def runtime_started_at_utc() -> str:
    return str(os.getenv("FIRECLOUD_ANALYSIS_STARTED_AT_UTC", "") or "").strip()


def cache_stamp_path(path: str | Path) -> Path:
    p = Path(path)
    return p.with_name(p.name + ".firecloud-cache.json")


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def atomic_write_bytes(path: str | Path, data: bytes) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(f".{p.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    try:
        with tmp.open("wb") as fh:
            fh.write(data)
            fh.flush()
            try:
                os.fsync(fh.fileno())
            except Exception:
                pass
        os.replace(tmp, p)
        return p
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except Exception:
                pass


def atomic_write_text(path: str | Path, text: str, encoding: str = "utf-8") -> Path:
    return atomic_write_bytes(path, text.encode(encoding))


def atomic_write_json(path: str | Path, payload) -> Path:
    return atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2, default=str))


def stamp_cache_artifact(path: str | Path, *, provider: str, role: str = "", schema: str = "", qc_state: str = "CACHE_READY", include_sha256: bool = False) -> dict:
    """Write durable provenance only after the cache artifact is complete/QC-ready."""
    p = Path(path)
    if not p.exists() or not p.is_file() or p.stat().st_size <= 0:
        return {}
    payload = {
        "provider": str(provider),
        "role": str(role),
        "schema": str(schema),
        "qc_state": str(qc_state),
        "cache_file": p.name,
        "byte_size": int(p.stat().st_size),
        "cache_created_at_utc": datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat(),
        "cache_source_job_id": runtime_job_id(),
        "cache_source_run_mode": runtime_cache_mode(),
        "cache_stamped_at_utc": utc_now_iso(),
    }
    if include_sha256:
        try:
            payload["sha256"] = sha256_file(p)
        except Exception:
            payload["sha256"] = ""
    try:
        atomic_write_json(cache_stamp_path(p), payload)
    except Exception:
        pass
    return payload


def read_cache_stamp(path: str | Path) -> dict:
    try:
        raw = json.loads(cache_stamp_path(path).read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    except Exception:
        return {}


def _parse_iso(text: str):
    try:
        return datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except Exception:
        return None


def cache_provenance(path: str | Path, *, provider: str = "", role: str = "", cache_status: str = "") -> dict:
    p = Path(path)
    now = datetime.now(timezone.utc)
    started = _parse_iso(runtime_started_at_utc())
    stamp = read_cache_stamp(p)
    exists = p.exists() and p.is_file()
    mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc) if exists else None
    source_job = str(stamp.get("cache_source_job_id", "") or "")
    current_job = runtime_job_id()
    if source_job and current_job:
        relation = "CURRENT_RUN_CACHE" if source_job == current_job else "PRIOR_RUN_PERSISTENT_CACHE"
    elif started is not None and mtime is not None:
        relation = "CURRENT_RUN_CACHE" if mtime >= started else "PRIOR_RUN_PERSISTENT_CACHE"
    else:
        relation = "UNKNOWN_CACHE_ORIGIN"
    return {
        "provider": str(provider or stamp.get("provider", "")),
        "role": str(role or stamp.get("role", "")),
        "cache_file": str(p),
        "cache_status": str(cache_status),
        "cache_exists": bool(exists),
        "cache_byte_size": int(p.stat().st_size) if exists else 0,
        "cache_created_at_utc": mtime.isoformat() if mtime else "",
        "cache_source_job_id": source_job,
        "cache_source_run_mode": str(stamp.get("cache_source_run_mode", "")),
        "current_job_id": current_job,
        "current_run_mode": runtime_cache_mode(),
        "cache_relation": relation,
        "cache_predates_current_job": bool(started is not None and mtime is not None and mtime < started),
        "cache_age_seconds": max(0.0, (now - mtime).total_seconds()) if mtime else None,
        "cache_qc_state": str(stamp.get("qc_state", "")),
        "cache_schema": str(stamp.get("schema", "")),
        "stamp_present": bool(stamp),
    }


def process_resource_snapshot() -> dict:
    """Best-effort Linux current/peak RSS and process diagnostics without psutil."""
    current_rss_kb = None
    peak_rss_kb = None
    threads = None
    vm_size_kb = None
    try:
        status = Path("/proc/self/status").read_text(encoding="utf-8", errors="replace")
        for line in status.splitlines():
            if line.startswith("VmRSS:"):
                current_rss_kb = int(line.split()[1])
            elif line.startswith("VmHWM:"):
                peak_rss_kb = int(line.split()[1])
            elif line.startswith("VmSize:"):
                vm_size_kb = int(line.split()[1])
            elif line.startswith("Threads:"):
                threads = int(line.split()[1])
    except Exception:
        pass
    try:
        ru = resource.getrusage(resource.RUSAGE_SELF)
        if peak_rss_kb is None:
            peak_rss_kb = int(ru.ru_maxrss)
    except Exception:
        pass
    child_count = None
    try:
        children = Path(f"/proc/{os.getpid()}/task/{os.getpid()}/children").read_text().strip()
        child_count = len(children.split()) if children else 0
    except Exception:
        pass
    return {
        "timestamp_utc": utc_now_iso(),
        "pid": os.getpid(),
        "rss_mb": (current_rss_kb / 1024.0) if current_rss_kb is not None else None,
        "peak_rss_mb": (peak_rss_kb / 1024.0) if peak_rss_kb is not None else None,
        "vm_size_mb": (vm_size_kb / 1024.0) if vm_size_kb is not None else None,
        "thread_count": threads,
        "child_process_count": child_count,
        "job_id": runtime_job_id(),
        "run_mode": runtime_cache_mode(),
    }


def dataframe_memory_mb(obj) -> float | None:
    try:
        return float(obj.memory_usage(index=True, deep=True).sum()) / (1024.0 * 1024.0)
    except Exception:
        return None
