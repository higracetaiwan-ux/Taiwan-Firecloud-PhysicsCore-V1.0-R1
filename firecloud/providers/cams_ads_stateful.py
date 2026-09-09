"""Stateful ECMWF ADS request supervision for PhysicsCore CAMS roles.

R5.7.34 separates remote ADS queue/processing lifetime from the local analysis
worker lifetime.  A local wait deadline never cancels the remote request.  The
opaque request_id is persisted with a deterministic request fingerprint so a
later worker can reattach via ``Client.get_remote(request_id)`` and download an
already-running/already-successful request instead of submitting a duplicate.

No credentials are ever written to the journal.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import time
import uuid
from typing import Any, Callable


TERMINAL_SUCCESS = {"successful", "succeeded", "completed", "complete"}
TERMINAL_FAILURE = {"failed", "unavailable", "cancelled", "canceled"}
QUEUE_STATES = {"accepted", "queued", "pending", "submitted"}
RUNNING_STATES = {"running", "in_progress", "in progress", "processing"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_request_fingerprint(dataset: str, request: dict[str, Any]) -> str:
    payload = json.dumps(
        {"dataset": str(dataset), "request": request},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _safe_role(role: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in str(role)).strip("_") or "unknown"


def request_journal_path(cache_dir: str | Path, role: str, fingerprint: str) -> Path:
    root = Path(cache_dir).expanduser() / "ads_remote_jobs" / _safe_role(role)
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{fingerprint[:24]}.json"


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.{uuid.uuid4().hex}.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
    os.replace(tmp, path)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        if not path.exists():
            return {}
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def normalized_remote_status(remote: Any) -> str:
    value = getattr(remote, "status", None)
    if callable(value):
        try:
            value = value()
        except TypeError:
            pass
    return str(value or "unknown").strip().lower().replace("-", "_")


def remote_request_id(remote: Any) -> str:
    for attr in ("request_id", "request_uid", "job_id"):
        value = getattr(remote, attr, None)
        if value:
            return str(value)
    return ""


@dataclass
class AdsStatefulTimeout(RuntimeError):
    role: str
    request_id: str
    remote_status: str
    reason: str
    total_elapsed_seconds: float
    queue_elapsed_seconds: float
    running_elapsed_seconds: float
    journal_path: str

    def __post_init__(self) -> None:
        RuntimeError.__init__(
            self,
            f"{self.reason}: role={self.role}; request_id={self.request_id}; "
            f"remote_status={self.remote_status}; elapsed={self.total_elapsed_seconds:.3f}s",
        )

    @property
    def audit_fields(self) -> dict[str, Any]:
        return {
            "ads_request_id": self.request_id,
            "ads_remote_status": self.remote_status,
            "ads_stateful_timeout_reason": self.reason,
            "ads_total_elapsed_seconds": round(self.total_elapsed_seconds, 3),
            "ads_queue_elapsed_seconds": round(self.queue_elapsed_seconds, 3),
            "ads_running_elapsed_seconds": round(self.running_elapsed_seconds, 3),
            "ads_request_recovery_eligible": bool(self.request_id),
            "ads_request_journal": self.journal_path,
        }


class AdsStatefulFailure(RuntimeError):
    def __init__(self, message: str, *, audit_fields: dict[str, Any] | None = None):
        super().__init__(message)
        self.audit_fields = dict(audit_fields or {})


def _refresh_remote(client: Any, request_id: str, current: Any) -> Any:
    getter = getattr(client, "get_remote", None)
    if callable(getter):
        return getter(request_id)
    # Test/backward-compatible escape hatch: some Remote implementations expose
    # update()/refresh().  The operational dependency is ecmwf-datastores-client
    # and therefore normally follows the get_remote() branch above.
    for name in ("update", "refresh"):
        fn = getattr(current, name, None)
        if callable(fn):
            result = fn()
            return current if result is None else result
    return current


def _download_remote(client: Any, remote: Any, request_id: str, target: Path) -> None:
    downloader = getattr(remote, "download", None)
    if callable(downloader):
        downloader(str(target))
        return
    client_download = getattr(client, "download_results", None)
    if callable(client_download):
        client_download(request_id, str(target))
        return
    raise AdsStatefulFailure(
        "ADS_REMOTE_DOWNLOAD_METHOD_UNAVAILABLE",
        audit_fields={"ads_request_id": request_id, "ads_remote_status": normalized_remote_status(remote)},
    )


def retrieve_with_stateful_deadline(
    *,
    client: Any,
    dataset: str,
    request: dict[str, Any],
    target: str | Path,
    role: str,
    cache_dir: str | Path,
    queue_grace_seconds: float = 75.0,
    running_grace_seconds: float = 120.0,
    total_deadline_seconds: float = 180.0,
    poll_seconds: float = 2.0,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Submit/reattach one ADS request and download it when successful.

    Queue and running deadlines are local *wait* deadlines only.  Exceeding one
    raises ``AdsStatefulTimeout`` while the remote job remains alive and its
    request ID remains journalled for the next worker/analysis run.
    """
    queue_grace_seconds = max(0.1, float(queue_grace_seconds))
    running_grace_seconds = max(0.1, float(running_grace_seconds))
    total_deadline_seconds = max(0.2, float(total_deadline_seconds))
    poll_seconds = max(0.05, float(poll_seconds))
    target = Path(target)
    fingerprint = canonical_request_fingerprint(dataset, request)
    journal_path = request_journal_path(cache_dir, role, fingerprint)
    journal = _load_json(journal_path)
    request_id = ""
    remote = None
    reattached = False

    # Reattach only when the journal is exactly for this request fingerprint.
    if journal.get("request_fingerprint") == fingerprint and journal.get("request_id"):
        candidate = str(journal.get("request_id"))
        try:
            remote = client.get_remote(candidate)
            status = normalized_remote_status(remote)
            if status not in TERMINAL_FAILURE:
                request_id = candidate
                reattached = True
            else:
                journal.update({"remote_status": status, "terminal_failure_at_utc": utc_now_iso()})
                _atomic_json(journal_path, journal)
                remote = None
        except Exception as exc:
            # A stale/expired remote is not silently treated as success.  It is
            # recorded, then one fresh submit is allowed for this invocation.
            journal.update({"reattach_error": f"{type(exc).__name__}: {exc}", "reattach_failed_at_utc": utc_now_iso()})
            _atomic_json(journal_path, journal)
            remote = None

    if remote is None:
        try:
            remote = client.submit(dataset, request)
        except TypeError:
            # Some released client versions accept the request as keyword fields.
            remote = client.submit(dataset, **request)
        request_id = remote_request_id(remote)
        if not request_id:
            raise AdsStatefulFailure("ADS_SUBMIT_RETURNED_NO_REQUEST_ID")
        journal = {
            "schema": "R5.7.34_ADS_STATEFUL_REQUEST_JOURNAL_V1",
            "role": str(role),
            "dataset": str(dataset),
            "request_fingerprint": fingerprint,
            "request_id": request_id,
            "submitted_at_utc": utc_now_iso(),
            "reattached": False,
            "remote_status": normalized_remote_status(remote),
            "status_history": [],
        }
        _atomic_json(journal_path, journal)

    started = monotonic()
    queue_started = started
    running_started: float | None = None
    last_status = ""
    status_history: list[dict[str, Any]] = list(journal.get("status_history") or [])

    while True:
        try:
            remote = _refresh_remote(client, request_id, remote)
            status = normalized_remote_status(remote)
        except Exception as exc:
            raise AdsStatefulFailure(
                f"ADS_REMOTE_STATUS_REFRESH_FAILED: {type(exc).__name__}: {exc}",
                audit_fields={
                    "ads_request_id": request_id,
                    "ads_request_recovery_eligible": True,
                    "ads_request_journal": str(journal_path),
                },
            ) from exc
        now = monotonic()
        total_elapsed = now - started
        if status != last_status:
            if status in RUNNING_STATES and running_started is None:
                running_started = now
            status_history.append({"status": status, "at_utc": utc_now_iso(), "elapsed_seconds": round(total_elapsed, 3)})
            last_status = status
        queue_elapsed = (running_started if running_started is not None else now) - queue_started
        running_elapsed = 0.0 if running_started is None else now - running_started
        journal.update({
            "request_id": request_id,
            "remote_status": status,
            "reattached": bool(reattached),
            "updated_at_utc": utc_now_iso(),
            "queue_elapsed_seconds": round(queue_elapsed, 3),
            "running_elapsed_seconds": round(running_elapsed, 3),
            "total_elapsed_seconds": round(total_elapsed, 3),
            "status_history": status_history[-32:],
        })
        _atomic_json(journal_path, journal)

        if status in TERMINAL_SUCCESS:
            target.parent.mkdir(parents=True, exist_ok=True)
            _download_remote(client, remote, request_id, target)
            journal.update({"remote_status": status, "downloaded_at_utc": utc_now_iso(), "target_name": target.name})
            _atomic_json(journal_path, journal)
            return {
                "ads_request_id": request_id,
                "ads_remote_status": status,
                "ads_request_reattached": reattached,
                "ads_request_recovery_eligible": False,
                "ads_request_journal": str(journal_path),
                "ads_queue_elapsed_seconds": round(queue_elapsed, 3),
                "ads_running_elapsed_seconds": round(running_elapsed, 3),
                "ads_total_elapsed_seconds": round(total_elapsed, 3),
                "ads_stateful_deadline_contract": "R5.7.34_QUEUE_RUNNING_TOTAL_PHASED_DEADLINE_V1",
            }
        if status in TERMINAL_FAILURE:
            raise AdsStatefulFailure(
                f"ADS_REMOTE_TERMINAL_FAILURE:{status}",
                audit_fields={
                    "ads_request_id": request_id,
                    "ads_remote_status": status,
                    "ads_request_recovery_eligible": False,
                    "ads_request_journal": str(journal_path),
                },
            )

        reason = ""
        if total_elapsed >= total_deadline_seconds:
            reason = "CAMS_ADS_STATEFUL_TOTAL_DEADLINE_EXCEEDED"
        elif running_started is None and queue_elapsed >= queue_grace_seconds:
            reason = "CAMS_ADS_QUEUE_GRACE_EXCEEDED"
        elif running_started is not None and running_elapsed >= running_grace_seconds:
            reason = "CAMS_ADS_RUNNING_GRACE_EXCEEDED"
        if reason:
            journal.update({"local_wait_deferred_at_utc": utc_now_iso(), "local_wait_deferred_reason": reason})
            _atomic_json(journal_path, journal)
            raise AdsStatefulTimeout(
                role=str(role), request_id=request_id, remote_status=status, reason=reason,
                total_elapsed_seconds=total_elapsed, queue_elapsed_seconds=queue_elapsed,
                running_elapsed_seconds=running_elapsed, journal_path=str(journal_path),
            )
        sleep(min(poll_seconds, max(0.05, total_deadline_seconds - total_elapsed)))
