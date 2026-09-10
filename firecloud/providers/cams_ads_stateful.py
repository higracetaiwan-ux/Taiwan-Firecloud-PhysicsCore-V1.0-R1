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
import re
import time
import uuid
import shutil
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from typing import Any, Callable


TERMINAL_SUCCESS = {"successful", "succeeded", "completed", "complete"}
TERMINAL_FAILURE = {"failed", "unavailable", "cancelled", "canceled"}
QUEUE_STATES = {"accepted", "queued", "pending", "submitted"}
RUNNING_STATES = {"running", "in_progress", "in progress", "processing"}
TRANSIENT_DOWNLOAD_HTTP_STATUS = {408, 429, 500, 502, 503, 504}


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


def _positive_env_float(name: str, default: float, minimum: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except Exception:
        value = float(default)
    return max(float(minimum), value)


def _positive_env_int(name: str, default: int, minimum: int = 1) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except Exception:
        value = int(default)
    return max(int(minimum), value)


def _download_recovery_policy() -> tuple[int, float, float, float]:
    """Return bounded post-success download retry settings.

    R5.7.38 intentionally keeps this policy separate from ADS queue/running
    deadlines.  The remote job is already terminal-successful at this point,
    so a transient download-node failure must never trigger another submit.
    """
    attempts = _positive_env_int("FIRECLOUD_CAMS_DOWNLOAD_MAX_ATTEMPTS", 4)
    initial = _positive_env_float("FIRECLOUD_CAMS_DOWNLOAD_INITIAL_BACKOFF_SECONDS", 2.0, 0.1)
    maximum = _positive_env_float("FIRECLOUD_CAMS_DOWNLOAD_MAX_BACKOFF_SECONDS", 12.0, initial)
    timeout = _positive_env_float("FIRECLOUD_CAMS_DOWNLOAD_HTTP_TIMEOUT_SECONDS", 45.0, 1.0)
    return attempts, initial, maximum, timeout


def _results_object(client: Any, remote: Any, request_id: str) -> Any | None:
    getter = getattr(client, "get_results", None)
    if callable(getter):
        return getter(request_id)
    getter = getattr(remote, "get_results", None)
    if callable(getter):
        return getter()
    return None


def _results_location(results: Any) -> str:
    if results is None:
        return ""
    value = getattr(results, "location", None)
    if callable(value):
        value = value()
    return str(value or "").strip()


def _retry_after_seconds(exc: BaseException) -> float | None:
    if not isinstance(exc, HTTPError):
        return None
    headers = getattr(exc, "headers", None)
    if headers is None:
        return None
    try:
        value = headers.get("Retry-After")
        if value is None:
            return None
        parsed = float(value)
        return parsed if parsed > 0 else None
    except Exception:
        return None


def _http_status_from_exception(exc: BaseException) -> int:
    if isinstance(exc, HTTPError):
        try:
            return int(getattr(exc, "code", 0) or 0)
        except Exception:
            return 0
    for value in (getattr(exc, "status_code", None), getattr(getattr(exc, "response", None), "status_code", None)):
        try:
            if value is not None:
                return int(value)
        except Exception:
            pass
    return 0


def _safe_download_error_text(exc: BaseException) -> str:
    # Signed result URLs may contain temporary access material.  Even when a
    # third-party exception embeds the URL in its message, never persist it.
    text = f"{type(exc).__name__}: {exc}"
    return re.sub(r"https?://[^\s]+", "<redacted-download-url>", text, flags=re.IGNORECASE)


def _transient_download_error(exc: BaseException) -> bool:
    status = _http_status_from_exception(exc)
    if status:
        return status in TRANSIENT_DOWNLOAD_HTTP_STATUS
    if isinstance(exc, (URLError, TimeoutError, ConnectionError, OSError)):
        return True
    # requests/httpx-style connection exceptions do not necessarily inherit
    # Python's built-in ConnectionError.  Keep this narrow and name-based.
    name = type(exc).__name__.lower()
    return "timeout" in name or "connectionerror" in name or "connecterror" in name


def _download_url_once(location: str, target: Path, timeout_seconds: float) -> int:
    """Download one signed ADS result URL without library-internal 120 s retry.

    The signed URL is deliberately never returned to callers or written to the
    request journal because it may contain temporary access material.
    """
    request = Request(location, headers={"User-Agent": "Taiwan-Firecloud-PhysicsCore/CAMS-download"})
    written = 0
    with urlopen(request, timeout=float(timeout_seconds)) as response, target.open("wb") as fh:
        status = int(getattr(response, "status", 200) or 200)
        if status < 200 or status >= 300:
            raise HTTPError(location, status, f"HTTP {status}", getattr(response, "headers", None), None)
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            fh.write(chunk)
            written += len(chunk)
    return written


def _download_remote_with_recovery(
    *,
    client: Any,
    remote: Any,
    request_id: str,
    target: Path,
    journal: dict[str, Any],
    journal_path: Path,
    monotonic: Callable[[], float],
    sleep: Callable[[float], None],
) -> dict[str, Any]:
    """Download terminal-successful ADS results with bounded retry.

    Preferred path reacquires ``Results`` from the *same* request ID on every
    attempt and downloads its current signed location directly.  This avoids
    the client downloader's long default retry sleep after a transient 502 and
    also allows a fresh download-node location to be selected.  If the client
    does not expose Results/location, the legacy native downloader is used once
    as a compatibility fallback.
    """
    max_attempts, initial_backoff, max_backoff, http_timeout = _download_recovery_policy()
    started = monotonic()
    retry_count = 0
    url_refresh_count = 0
    total_backoff = 0.0
    errors: list[str] = []
    strategy = "DIRECT_RESULTS_LOCATION_BOUNDED_RETRY_V1"

    for attempt in range(1, max_attempts + 1):
        if target.exists():
            try:
                target.unlink()
            except Exception:
                pass
        try:
            results = _results_object(client, remote, request_id)
            location = _results_location(results)
            if location:
                url_refresh_count += 1
                _download_url_once(location, target, http_timeout)
            else:
                # Compatibility fallback for older/test clients only.  Do not
                # loop this path because the library itself may have a long
                # internal retry policy.
                strategy = "CLIENT_NATIVE_DOWNLOAD_FALLBACK_ONCE"
                downloader = getattr(remote, "download", None)
                if callable(downloader):
                    downloader(str(target))
                else:
                    client_download = getattr(client, "download_results", None)
                    if callable(client_download):
                        client_download(request_id, str(target))
                    else:
                        raise AdsStatefulFailure(
                            "ADS_REMOTE_DOWNLOAD_METHOD_UNAVAILABLE",
                            audit_fields={
                                "ads_request_id": request_id,
                                "ads_remote_status": normalized_remote_status(remote),
                            },
                        )
            elapsed = monotonic() - started
            meta = {
                "ads_download_strategy": strategy,
                "ads_download_attempts": attempt,
                "ads_download_retry_count": retry_count,
                "ads_download_url_refresh_count": url_refresh_count,
                "ads_download_backoff_seconds": round(total_backoff, 3),
                "ads_download_elapsed_seconds": round(elapsed, 3),
                "ads_download_http_timeout_seconds": round(http_timeout, 3),
                "ads_download_last_error": errors[-1] if errors else "",
                "ads_download_recovery_contract": "R5.7.38_POST_SUCCESS_SAME_REQUEST_ID_BOUNDED_DOWNLOAD_RETRY_V1",
            }
            journal.update(meta)
            journal["download_attempt_history"] = (list(journal.get("download_attempt_history") or []) + [{
                "attempt": attempt, "status": "SUCCESS", "at_utc": utc_now_iso(),
                "elapsed_seconds": round(elapsed, 3), "strategy": strategy,
            }])[-16:]
            _atomic_json(journal_path, journal)
            return meta
        except AdsStatefulFailure:
            raise
        except Exception as exc:
            error_text = _safe_download_error_text(exc)
            errors.append(error_text)
            transient = _transient_download_error(exc)
            elapsed = monotonic() - started
            history = list(journal.get("download_attempt_history") or [])
            history.append({
                "attempt": attempt, "status": "RETRYABLE_FAILURE" if transient else "NON_RETRYABLE_FAILURE",
                "at_utc": utc_now_iso(), "elapsed_seconds": round(elapsed, 3),
                "error_type": type(exc).__name__,
                "http_status": _http_status_from_exception(exc) or None,
            })
            journal.update({
                "download_attempt_history": history[-16:],
                "ads_download_strategy": strategy,
                "ads_download_attempts": attempt,
                "ads_download_retry_count": retry_count,
                "ads_download_url_refresh_count": url_refresh_count,
                "ads_download_backoff_seconds": round(total_backoff, 3),
                "ads_download_elapsed_seconds": round(elapsed, 3),
                "ads_download_last_error": error_text,
            })
            _atomic_json(journal_path, journal)
            if strategy == "CLIENT_NATIVE_DOWNLOAD_FALLBACK_ONCE" or not transient or attempt >= max_attempts:
                raise AdsStatefulFailure(
                    f"ADS_POST_SUCCESS_DOWNLOAD_FAILED: {error_text}",
                    audit_fields={
                        "ads_request_id": request_id,
                        "ads_remote_status": normalized_remote_status(remote),
                        "ads_request_recovery_eligible": True,
                        "ads_download_recovery_eligible": True,
                        "ads_request_journal": str(journal_path),
                        "ads_download_strategy": strategy,
                        "ads_download_attempts": attempt,
                        "ads_download_retry_count": retry_count,
                        "ads_download_url_refresh_count": url_refresh_count,
                        "ads_download_backoff_seconds": round(total_backoff, 3),
                        "ads_download_elapsed_seconds": round(elapsed, 3),
                        "ads_download_last_error": error_text,
                        "ads_download_recovery_contract": "R5.7.38_POST_SUCCESS_SAME_REQUEST_ID_BOUNDED_DOWNLOAD_RETRY_V1",
                    },
                ) from exc
            retry_count += 1
            backoff = min(max_backoff, initial_backoff * (2 ** (attempt - 1)))
            server_retry = _retry_after_seconds(exc)
            if server_retry is not None:
                # Honor server guidance only up to the bounded cap.  A 120 s
                # Retry-After must not silently reintroduce the field-observed
                # 120 s stall this recovery layer exists to remove.
                backoff = max(backoff, min(max_backoff, server_retry))
            total_backoff += backoff
            sleep(backoff)

    raise AssertionError("unreachable")


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
            download_meta = _download_remote_with_recovery(
                client=client, remote=remote, request_id=request_id, target=target,
                journal=journal, journal_path=journal_path, monotonic=monotonic, sleep=sleep,
            )
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
                **download_meta,
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
