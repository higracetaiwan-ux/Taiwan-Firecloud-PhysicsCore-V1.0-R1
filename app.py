from datetime import date, datetime, timezone
import os
import io
import json
import re
import zipfile
import pickle
import uuid
import subprocess
import tempfile
import sys
import time
from pathlib import Path
from time import perf_counter

import pandas as pd
import streamlit as st

from firecloud import PROGRAM_NAME, __version__, __baseline__
from firecloud.hitran_readiness import hitran_backend_status, resolve_hitran_db_path, resolve_hitran_lut_path
from firecloud.hitran_runtime import (
    COEFFICIENT_FILENAME as HITRAN_LUT_FILENAME,
    MANIFEST_FILENAME as HITRAN_MANIFEST_FILENAME,
    install_runtime_lut,
    copy_built_lut_to_runtime,
)
from firecloud.visuals import (
    cross_section_figure,
    route_map_figure,
    illumination_matrix_figure,
    dynamic_rez_figure,
    forecast_voxel_illumination_figure,
    reconstructed_voxel_figure,
)

def _bridge_streamlit_ads_secrets() -> None:
    """Map Streamlit secrets to the provider environment without logging keys.

    Supported forms in .streamlit/secrets.toml / Streamlit Cloud Secrets:
      ADS_API_KEY = "..."
      ADS_API_URL = "https://ads.atmosphere.copernicus.eu/api"   # optional
    or:
      [cams_ads]
      key = "..."
      url = "https://ads.atmosphere.copernicus.eu/api"          # optional
    """
    try:
        secrets = st.secrets
        key = secrets.get("ADS_API_KEY")
        url = secrets.get("ADS_API_URL")
        if not key and "cams_ads" in secrets:
            section = secrets["cams_ads"]
            key = section.get("key")
            url = section.get("url")
        if key and not os.getenv("ADS_API_KEY"):
            os.environ["ADS_API_KEY"] = str(key)
        if url and not os.getenv("ADS_API_URL"):
            os.environ["ADS_API_URL"] = str(url)
    except Exception:
        # No secrets file / restricted secret access is a normal deployment state.
        pass


_bridge_streamlit_ads_secrets()

def _bridge_streamlit_hitran_secrets() -> None:
    """Expose HITRAN secrets to isolated builder subprocesses without logging them."""
    try:
        secrets = st.secrets
        key = secrets.get("HITRAN_API_KEY")
        db_path = secrets.get("FIRECLOUD_HITRAN_DB")
        lut_path = secrets.get("FIRECLOUD_HITRAN_LUT_PATH")
        if "hitran" in secrets:
            section = secrets["hitran"]
            key = key or section.get("api_key") or section.get("key")
            db_path = db_path or section.get("db_path") or section.get("path")
            lut_path = lut_path or section.get("lut_path") or section.get("runtime_lut_path")
        if key and not os.getenv("HITRAN_API_KEY"):
            os.environ["HITRAN_API_KEY"] = str(key).strip()
        if db_path and not os.getenv("FIRECLOUD_HITRAN_DB"):
            os.environ["FIRECLOUD_HITRAN_DB"] = str(db_path).strip()
        if lut_path and not os.getenv("FIRECLOUD_HITRAN_LUT_PATH"):
            os.environ["FIRECLOUD_HITRAN_LUT_PATH"] = str(lut_path).strip()
    except Exception:
        pass


def _kill_process_tree(proc: subprocess.Popen) -> None:
    """Best-effort hard stop of the builder process tree.

    Streamlit Cloud runs on Linux, where the child is launched in a dedicated
    process session. Killing the process group prevents HAPI/HAPI2 descendants
    from surviving a Python timeout and keeping the deployment busy forever.
    """
    import signal
    try:
        if os.name == "posix":
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                return
            try:
                proc.wait(timeout=3)
                return
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        else:
            proc.kill()
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def _tail_text(path: Path, max_chars: int = 12000) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""
    return text[-max_chars:]


def _run_hitran_builder_step(
    command: list[str],
    timeout_seconds: int,
    progress_callback=None,
    label: str = "HITRAN",
) -> tuple[bool, str, float, bool]:
    """Run one builder step with a real wall-clock deadline and tree kill.

    stdout goes to a temporary file rather than PIPE so a verbose downloader
    cannot deadlock on a full pipe. The caller receives periodic elapsed-time
    updates while the subprocess runs.
    """
    import time
    t0 = time.monotonic()
    log_path = None
    proc = None
    try:
        with tempfile.NamedTemporaryFile(prefix="firecloud_hitran_", suffix=".log", delete=False) as tf:
            log_path = Path(tf.name)
            proc = subprocess.Popen(
                command,
                cwd=str(Path(__file__).resolve().parent),
                env=os.environ.copy(),
                stdout=tf,
                stderr=subprocess.STDOUT,
                text=False,
                start_new_session=(os.name == "posix"),
            )
        last_update = -1
        while proc.poll() is None:
            elapsed = time.monotonic() - t0
            sec = int(elapsed)
            if sec != last_update and progress_callback is not None:
                last_update = sec
                remaining = max(0, int(timeout_seconds - elapsed))
                live_label = label
                try:
                    tail = _tail_text(log_path, 5000)
                    lines = [ln.strip() for ln in tail.splitlines() if ln.strip().startswith(("FC_PROGRESS ", "FC_PROGRESS_DONE ", "NARROW_TABLE_"))]
                    if lines:
                        detail = lines[-1]
                        if detail.startswith("FC_PROGRESS_DONE "):
                            detail = detail.replace("FC_PROGRESS_DONE ", "完成 ", 1)
                        elif detail.startswith("FC_PROGRESS "):
                            detail = detail.replace("FC_PROGRESS ", "進度 ", 1)
                        elif detail.startswith("NARROW_TABLE_READY "):
                            detail = detail.replace("NARROW_TABLE_READY ", "窄頻表 ", 1)
                        live_label = f"{label}｜{detail}"
                except Exception:
                    pass
                progress_callback(live_label, elapsed, remaining)
            if elapsed >= timeout_seconds:
                _kill_process_tree(proc)
                elapsed = time.monotonic() - t0
                out = _tail_text(log_path, 10000)
                return False, out + f"\nHARD_TIMEOUT_TREE_KILLED after {elapsed:.1f}s (limit {timeout_seconds}s)", elapsed, True
            time.sleep(0.5)
        elapsed = time.monotonic() - t0
        out = _tail_text(log_path, 12000)
        return proc.returncode == 0, out, elapsed, False
    except Exception as exc:
        if proc is not None and proc.poll() is None:
            _kill_process_tree(proc)
        elapsed = time.monotonic() - t0
        out = _tail_text(log_path, 8000) if log_path else ""
        return False, out + f"\n{type(exc).__name__}: {exc}", elapsed, False
    finally:
        if log_path is not None:
            try:
                log_path.unlink(missing_ok=True)
            except Exception:
                pass


def _env_timeout(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(float(os.environ.get(name, default)))
    except Exception:
        value = default
    return max(minimum, min(maximum, value))


def _hitran_one_click_bootstrap(progress_callback=None) -> tuple[bool, str]:
    """Build local spectroscopy with bounded, observable stages.

    Each H2O/O2 download is isolated in its own process, so a stalled HITRAN
    request cannot hold the entire bootstrap forever. Existing line tables are
    skipped by the helper. The validated packaged O3 XSC is used as a build
    input when no database-local copy exists. The LUT build is hard-bounded.
    """
    root = Path(__file__).resolve().parent
    db_path = os.environ.get("FIRECLOUD_HITRAN_DB", "hitran_db").strip() or "hitran_db"
    packaged_o3_xsc = root / "spectroscopy_sources" / "O3_SerdyuchenkoGorshelev_213_1100nm.dat"
    o3_xsc_arg = str(packaged_o3_xsc) if packaged_o3_xsc.is_file() else "O3_SerdyuchenkoGorshelev_213_1100nm.dat"
    download_timeout = _env_timeout("FIRECLOUD_HITRAN_GAS_TIMEOUT_SECONDS", 240, 30, 900)
    build_timeout = _env_timeout("FIRECLOUD_HITRAN_LUT_TIMEOUT_SECONDS", 3600, 60, 7200)
    audit_timeout = 30
    logs: list[str] = []

    for gas in ("H2O", "O2"):
        ok, out, elapsed, timed_out = _run_hitran_builder_step(
            [sys.executable, str(root / "bootstrap_hitran_local_db.py"), "--db", db_path, "--download-gas", gas],
            timeout_seconds=download_timeout,
            progress_callback=progress_callback,
            label=f"下載 {gas} line transitions",
        )
        logs.append(f"=== HITRAN {gas} DOWNLOAD ({elapsed:.1f}s, timeout={timed_out}) ===\n" + out)
        if not ok:
            return False, "\n\n".join(logs)

    ok, out, elapsed, timed_out = _run_hitran_builder_step(
        [sys.executable, str(root / "build_hitran_band_coefficients.py"), "--db", db_path,
         "--h2o-table", "H2O_535_765", "--o2-table", "O2_535_765",
         "--o3-xsc", o3_xsc_arg,
         "--v1-six-band",
         "--incremental-base-lut", str(root / "hitran_runtime" / HITRAN_LUT_FILENAME),
         "--incremental-base-manifest", str(root / "hitran_runtime" / HITRAN_MANIFEST_FILENAME)],
        timeout_seconds=build_timeout,
        progress_callback=progress_callback,
        label="R4.8.2 窄頻建立 PhysicsCore 550 nm coefficient（沿用已驗證 575–750 nm）",
    )
    logs.append(f"=== FIRECLOUD LUT BUILD ({elapsed:.1f}s, timeout={timed_out}) ===\n" + out)
    if not ok:
        return False, "\n\n".join(logs)

    ok, out, elapsed, timed_out = _run_hitran_builder_step(
        [sys.executable, str(root / "bootstrap_hitran_local_db.py"), "--db", db_path],
        timeout_seconds=audit_timeout,
        progress_callback=progress_callback,
        label="readiness audit",
    )
    logs.append(f"=== READINESS AUDIT ({elapsed:.1f}s, timeout={timed_out}) ===\n" + out)
    return ok and ("READY_LOCAL_HITRAN_LUT_550NM" in out), "\n\n".join(logs)


def _hitran_build_lut_only(progress_callback=None) -> tuple[bool, str]:
    root = Path(__file__).resolve().parent
    db_path = os.environ.get("FIRECLOUD_HITRAN_DB", "hitran_db").strip() or "hitran_db"
    packaged_o3_xsc = root / "spectroscopy_sources" / "O3_SerdyuchenkoGorshelev_213_1100nm.dat"
    o3_xsc_arg = str(packaged_o3_xsc) if packaged_o3_xsc.is_file() else "O3_SerdyuchenkoGorshelev_213_1100nm.dat"
    build_timeout = _env_timeout("FIRECLOUD_HITRAN_LUT_TIMEOUT_SECONDS", 3600, 60, 7200)
    logs = []
    ok, out, elapsed, timed_out = _run_hitran_builder_step(
        [sys.executable, str(root / "build_hitran_band_coefficients.py"), "--db", db_path,
         "--h2o-table", "H2O_535_765", "--o2-table", "O2_535_765",
         "--o3-xsc", o3_xsc_arg,
         "--v1-six-band",
         "--incremental-base-lut", str(root / "hitran_runtime" / HITRAN_LUT_FILENAME),
         "--incremental-base-manifest", str(root / "hitran_runtime" / HITRAN_MANIFEST_FILENAME)],
        timeout_seconds=build_timeout,
        progress_callback=progress_callback,
        label="R4.8.2 窄頻建立 PhysicsCore 550 nm coefficient（沿用已驗證 575–750 nm）",
    )
    logs.append(f"=== FIRECLOUD LUT BUILD ({elapsed:.1f}s, timeout={timed_out}) ===\n" + out)
    if not ok:
        return False, "\n\n".join(logs)
    ok, out, elapsed, timed_out = _run_hitran_builder_step(
        [sys.executable, str(root / "bootstrap_hitran_local_db.py"), "--db", db_path],
        timeout_seconds=30,
        progress_callback=progress_callback,
        label="readiness audit",
    )
    logs.append(f"=== READINESS AUDIT ({elapsed:.1f}s, timeout={timed_out}) ===\n" + out)
    return ok and ("READY_LOCAL_HITRAN_LUT_550NM" in out), "\n\n".join(logs)


def _import_manual_hitran_par(gas: str, uploaded_bytes: bytes, original_name: str = "") -> tuple[bool, str]:
    """Import one browser-downloaded HITRAN standard .par/text line list.

    This is the operational fallback when both documented library download paths
    fail remotely.  The file is validated and converted by the isolated helper;
    no user spectroscopy is silently accepted as READY without HAPI parsing.
    """
    root = Path(__file__).resolve().parent
    db_path = os.environ.get("FIRECLOUD_HITRAN_DB", "hitran_db").strip() or "hitran_db"
    if gas not in {"H2O", "O3", "O2"}:
        return False, f"Unsupported gas: {gas}"
    if not uploaded_bytes:
        return False, "Uploaded file is empty."
    suffix = Path(original_name or "manual.par").suffix.lower()
    if suffix not in {".par", ".txt", ".data"}:
        suffix = ".par"
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(prefix=f"hitran_{gas.lower()}_", suffix=suffix, delete=False) as tf:
            tf.write(uploaded_bytes)
            tmp = Path(tf.name)
        ok, out, elapsed, timed_out = _run_hitran_builder_step(
            [sys.executable, str(root / "bootstrap_hitran_local_db.py"), "--db", db_path,
             "--import-par-gas", gas, "--import-par-file", str(tmp)],
            timeout_seconds=120,
            label=f"匯入 {gas} HITRAN .par",
        )
        log = f"=== MANUAL HITRAN {gas} IMPORT ({elapsed:.1f}s, timeout={timed_out}) ===\n{out}"
        return ok, log
    finally:
        if tmp is not None:
            try:
                tmp.unlink(missing_ok=True)
            except Exception:
                pass



def _import_o3_serdyuchenko_xsc(uploaded_bytes: bytes, original_name: str = "") -> tuple[bool, str]:
    """Validate and store the Serdyuchenko–Gorshelev O3 XSC source file.

    Runtime never consumes this raw file directly after the hybrid LUT is built.
    """
    db_path = Path(os.environ.get("FIRECLOUD_HITRAN_DB", "hitran_db").strip() or "hitran_db").expanduser()
    db_path.mkdir(parents=True, exist_ok=True)
    if not uploaded_bytes:
        return False, "Uploaded O3 XSC file is empty."
    try:
        text = uploaded_bytes.decode("utf-8", errors="replace")
        rows = []
        for line in text.splitlines():
            t = line.strip()
            if not t or not (t[0].isdigit() or t[0] in "+-"):
                continue
            parts = t.split()
            if len(parts) < 12:
                continue
            try:
                vals = [float(x) for x in parts[:12]]
            except ValueError:
                continue
            rows.append(vals)
        if not rows:
            return False, "O3_XSC_NO_NUMERIC_ROWS"
        import numpy as _np
        arr = _np.asarray(rows, float)
        wl = arr[:, 0]
        band = (wl >= 562.5) & (wl <= 762.5)
        if int(band.sum()) < 10000:
            return False, f"O3_XSC_575_750_COVERAGE_INSUFFICIENT:{int(band.sum())}_rows"
        if not _np.isfinite(arr[band, 1:12]).all() or (arr[band, 1:12] < 0).any():
            return False, "O3_XSC_NONFINITE_OR_NEGATIVE"
        out = db_path / "O3_SerdyuchenkoGorshelev_213_1100nm.dat"
        out.write_bytes(uploaded_bytes)
        return True, json.dumps({
            "status": "READY_O3_SERDYUCHENKO_GORSHELEV_XSC",
            "source_file": original_name,
            "installed_path": str(out),
            "numeric_rows": int(len(arr)),
            "rows_562_5_762_5nm": int(band.sum()),
            "wavelength_min_nm": float(_np.nanmin(wl)),
            "wavelength_max_nm": float(_np.nanmax(wl)),
            "temperatures_k": [293,283,273,263,253,243,233,223,213,203,193],
        }, ensure_ascii=False, indent=2)
    except Exception as exc:
        return False, f"O3_XSC_IMPORT_FAILED:{type(exc).__name__}:{exc}"

def _hitran_runtime_dir() -> Path:
    return Path(__file__).resolve().parent / "hitran_runtime"


def _promote_built_hitran_lut() -> tuple[bool, str]:
    db_path = resolve_hitran_db_path()[0]
    audit = copy_built_lut_to_runtime(db_path, _hitran_runtime_dir())
    if audit.get("ok"):
        return True, json.dumps(audit, ensure_ascii=False, indent=2)
    return False, json.dumps(audit, ensure_ascii=False, indent=2)


def _install_uploaded_hitran_runtime_lut(csv_bytes: bytes, manifest_bytes: bytes | None) -> tuple[bool, str]:
    audit = install_runtime_lut(csv_bytes, manifest_bytes, _hitran_runtime_dir())
    return bool(audit.get("ok")), json.dumps(audit, ensure_ascii=False, indent=2)


def _runtime_lut_download_payloads():
    path, _source = resolve_hitran_lut_path()
    if not path.is_file():
        return None, None
    csv_bytes = path.read_bytes()
    manifest = path.parent / HITRAN_MANIFEST_FILENAME
    manifest_bytes = manifest.read_bytes() if manifest.is_file() else None
    return csv_bytes, manifest_bytes


_bridge_streamlit_hitran_secrets()


# V8.4.10.5 persistent analysis journal / session recovery -----------------------
_STATE_DIR = Path(os.environ.get("FIRECLOUD_STATE_DIR", ".firecloud_state")).expanduser()
_JOB_STATE_PATH = _STATE_DIR / "analysis_job_state.json"
_RESULT_STATE_PATH = _STATE_DIR / "last_analysis_result.pkl"


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _load_analysis_job_state() -> dict:
    try:
        raw = json.loads(_JOB_STATE_PATH.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    except Exception:
        return {}


def _load_cams_worker_checkpoint() -> dict:
    """Load the last external CAMS worker heartbeat for recovery diagnostics."""
    try:
        path = _STATE_DIR / "cams_worker_checkpoint.json"
        raw = json.loads(path.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    except Exception:
        return {}


def _load_all_cams_worker_checkpoints() -> dict:
    """Load latest plus role-specific CAMS checkpoints for CASE evidence."""
    out = {}
    try:
        _started_cutoff = None
        _job = _load_analysis_job_state()
        _started_text = str(_job.get("worker_started_at_utc", "") or "")
        if _started_text:
            _started_cutoff = datetime.fromisoformat(_started_text.replace("Z", "+00:00")).timestamp() - 2.0
        for path in sorted(_STATE_DIR.glob("cams_worker_checkpoint_*.json")):
            if _started_cutoff is not None and path.stat().st_mtime < _started_cutoff:
                continue
            raw = _read_json_file(path)
            if raw:
                out[path.stem.removeprefix("cams_worker_checkpoint_")] = raw
    except Exception:
        pass
    latest = _load_cams_worker_checkpoint()
    if latest:
        out["latest"] = latest
    return out


def _save_analysis_job_state(state: dict) -> None:
    payload = dict(state)
    payload["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    try:
        _atomic_write_text(_JOB_STATE_PATH, json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    except Exception:
        # Recovery is best-effort and must never block the physics run.
        pass


def _save_completed_analysis_result(result: dict) -> bool:
    """Persist the last completed result so a Streamlit session reset can restore it."""
    try:
        _STATE_DIR.mkdir(parents=True, exist_ok=True)
        tmp = _RESULT_STATE_PATH.with_suffix(_RESULT_STATE_PATH.suffix + ".tmp")
        with tmp.open("wb") as fh:
            pickle.dump(result, fh, protocol=pickle.HIGHEST_PROTOCOL)
            fh.flush()
            try:
                os.fsync(fh.fileno())
            except Exception:
                pass
        os.replace(tmp, _RESULT_STATE_PATH)
        return True
    except Exception:
        return False


def _load_completed_analysis_result():
    try:
        with _RESULT_STATE_PATH.open("rb") as fh:
            out = pickle.load(fh)
        return out if isinstance(out, dict) else None
    except Exception:
        return None


def _job_paths(job_id: str) -> dict[str, Path]:
    job_dir = _STATE_DIR / "analysis_jobs" / str(job_id)
    return {
        "dir": job_dir,
        "request": job_dir / "request.json",
        "result": job_dir / "result.pkl",
        "progress": job_dir / "progress.json",
        "stdout": job_dir / "worker.stdout.log",
        "stderr": job_dir / "worker.stderr.log",
    }


def _read_json_file(path: Path) -> dict:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    except Exception:
        return {}


def _pid_alive(pid) -> bool:
    try:
        os.kill(int(pid), 0)
        return True
    except Exception:
        return False


def _launch_analysis_worker(request: dict, job_state: dict):
    paths = _job_paths(job_state["job_id"])
    paths["dir"].mkdir(parents=True, exist_ok=True)
    paths["request"].write_text(json.dumps(request, ensure_ascii=False, indent=2), encoding="utf-8")
    _atomic_write_text(paths["progress"], json.dumps({
        "status": "STARTING", "progress_fraction": 0.0,
        "last_message": "背景分析 worker 啟動中",
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
    }, ensure_ascii=False, indent=2))
    cmd = [sys.executable, "-m", "firecloud.analysis_worker",
           str(paths["request"]), str(paths["result"]), str(paths["progress"])]
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    env["FIRECLOUD_STATE_DIR"] = str(_STATE_DIR.resolve())
    job_state.update({
        "execution_mode": "EXTERNAL_ANALYSIS_WORKER",
        "worker_status": "STARTING",
        "worker_pid": None,
        "worker_request_path": str(paths["request"]),
        "worker_result_path": str(paths["result"]),
        "worker_progress_path": str(paths["progress"]),
        "worker_stdout_path": str(paths["stdout"]),
        "worker_stderr_path": str(paths["stderr"]),
        "worker_last_heartbeat_at_utc": datetime.now(timezone.utc).isoformat(),
        "worker_elapsed_seconds": 0.0,
        "last_message": "背景分析 worker 啟動中",
    })
    # Save the paths before Popen.  If the Streamlit parent is interrupted in
    # the narrow launch window, the next run can still find the request/logs.
    _save_analysis_job_state(job_state)
    proc = None
    out_fh = paths["stdout"].open("ab")
    err_fh = paths["stderr"].open("ab")
    try:
        proc = subprocess.Popen(
            cmd, stdout=out_fh, stderr=err_fh, env=env,
            cwd=str(Path(__file__).resolve().parent),
            start_new_session=(os.name == "posix"),
        )
    except Exception as exc:
        job_state.update({
            "status": "FAILED", "worker_status": "FAILED", "worker_exit_code": None,
            "error": f"ANALYSIS_WORKER_START_FAILED: {type(exc).__name__}: {exc}",
            "last_message": f"ANALYSIS_WORKER_START_FAILED: {type(exc).__name__}: {exc}",
            "worker_stderr_tail": _tail_text(paths["stderr"], 8000),
        })
        _save_analysis_job_state(job_state)
        raise
    finally:
        out_fh.close()
        err_fh.close()
    job_state.update({
        "status": "RUNNING", "worker_status": "STARTED", "worker_pid": proc.pid,
        "worker_started_at_utc": datetime.now(timezone.utc).isoformat(),
        "last_message": "背景分析 worker 已啟動",
    })
    _save_analysis_job_state(job_state)
    return proc, paths


def _load_worker_result(path: Path):
    try:
        with path.open("rb") as fh:
            result = pickle.load(fh)
        return result if isinstance(result, dict) else None
    except Exception:
        return None


def _reconcile_persisted_analysis_job(state: dict) -> dict:
    """Reconcile the journal with a worker that finished before a rerun.

    Streamlit can rerun between the worker's final progress write and the
    parent's journal write. In that narrow window the progress file is already
    COMPLETED while ``analysis_job_state.json`` still says RUNNING/FAILED,
    which incorrectly shows the recovery banner on the next page load.
    """
    if not isinstance(state, dict) or not state.get("worker_progress_path"):
        return state if isinstance(state, dict) else {}
    progress = _read_json_file(Path(str(state["worker_progress_path"])))
    progress_status = str(progress.get("status", "")).upper()
    result_path = Path(str(state.get("worker_result_path", ""))) if state.get("worker_result_path") else None
    if progress_status == "COMPLETED" and result_path is not None and result_path.is_file():
        state.update({
            "status": "COMPLETED",
            "worker_status": "COMPLETED",
            "progress_fraction": 1.0,
            "last_message": "分析完成",
            "worker_pid": progress.get("worker_pid", state.get("worker_pid")),
            "worker_last_heartbeat_at_utc": progress.get("updated_at_utc", state.get("worker_last_heartbeat_at_utc", "")),
            "worker_elapsed_seconds": progress.get("elapsed_seconds", state.get("worker_elapsed_seconds", 0.0)),
            "worker_exit_code": progress.get("exit_code", state.get("worker_exit_code", 0)),
            "worker_stderr_tail": _tail_text(Path(str(state.get("worker_stderr_path", ""))), 8000),
        })
        _save_analysis_job_state(state)
    elif progress_status == "FAILED" and str(state.get("status", "")).upper() in {"RUNNING", "STARTING"}:
        state.update({
            "status": "FAILED",
            "worker_status": "FAILED",
            "last_message": str(progress.get("last_message") or progress.get("error") or "背景分析 worker 失敗"),
            "error": str(progress.get("error") or progress.get("last_message") or "背景分析 worker 失敗"),
            "worker_exit_code": progress.get("exit_code", state.get("worker_exit_code")),
            "worker_stderr_tail": _tail_text(Path(str(state.get("worker_stderr_path", ""))), 8000),
        })
        _save_analysis_job_state(state)
    return state


def _monitor_analysis_worker(job_state: dict, progress, status_box, proc=None):
    """Follow a detached analysis worker and recover its result after reruns."""
    progress_path = Path(job_state["worker_progress_path"])
    result_path = Path(job_state["worker_result_path"])
    while True:
        pstate = _read_json_file(progress_path)
        if pstate:
            try:
                frac = max(0.0, min(1.0, float(pstate.get("progress_fraction", 0.0) or 0.0)))
            except (TypeError, ValueError):
                frac = 0.0
            message = str(pstate.get("last_message", "背景分析進行中"))
            progress.progress(int(round(frac * 100)), text=message)
            status_box.caption(message)
            worker_exit = pstate.get("exit_code")
            if worker_exit is None and proc is not None and proc.poll() is not None:
                worker_exit = proc.poll()
            job_state.update({
                "status": str(pstate.get("status", "RUNNING")),
                "worker_status": str(pstate.get("status", "RUNNING")),
                "worker_pid": pstate.get("worker_pid", job_state.get("worker_pid")),
                "progress_fraction": frac,
                "last_message": message,
                "worker_last_heartbeat_at_utc": pstate.get("updated_at_utc", ""),
                "worker_elapsed_seconds": pstate.get("elapsed_seconds", 0.0),
                "worker_exit_code": worker_exit,
                "worker_stderr_tail": _tail_text(Path(job_state.get("worker_stderr_path", "")), 8000),
            })
            if pstate.get("traceback"):
                job_state["worker_traceback"] = str(pstate["traceback"])[-12000:]
            _save_analysis_job_state(job_state)

        status = str(pstate.get("status", "RUNNING")).upper()
        if status == "COMPLETED" and result_path.exists():
            result = _load_worker_result(result_path)
            if result is not None:
                _save_completed_analysis_result(result)
                job_state.update({
                    "status": "COMPLETED", "worker_status": "COMPLETED",
                    "progress_fraction": 1.0, "last_message": "分析完成",
                    "worker_exit_code": pstate.get("exit_code", proc.poll() if proc is not None else 0),
                    "worker_stderr_tail": _tail_text(Path(job_state.get("worker_stderr_path", "")), 8000),
                })
                _save_analysis_job_state(job_state)
                return result
        if status == "FAILED":
            error = str(pstate.get("error") or pstate.get("last_message") or "背景分析 worker 失敗")
            job_state.update({
                "status": "FAILED", "worker_status": "FAILED", "error": error,
                "last_message": error,
                "worker_exit_code": pstate.get("exit_code", proc.poll() if proc is not None else None),
                "worker_stderr_tail": _tail_text(Path(job_state.get("worker_stderr_path", "")), 8000),
            })
            _save_analysis_job_state(job_state)
            raise RuntimeError(error)

        alive = proc.poll() is None if proc is not None else _pid_alive(job_state.get("worker_pid"))
        if not alive:
            if result_path.exists():
                result = _load_worker_result(result_path)
                if result is not None:
                    job_state.update({
                        "status": "COMPLETED", "worker_status": "COMPLETED",
                        "progress_fraction": 1.0, "last_message": "分析完成",
                        "worker_exit_code": proc.poll() if proc is not None else job_state.get("worker_exit_code"),
                        "worker_stderr_tail": _tail_text(Path(job_state.get("worker_stderr_path", "")), 8000),
                    })
                    _save_completed_analysis_result(result)
                    _save_analysis_job_state(job_state)
                    return result
            error = f"背景分析 worker 已結束但沒有結果（PID {job_state.get('worker_pid')}）"
            job_state.update({
                "status": "FAILED", "worker_status": "FAILED", "error": error,
                "last_message": error,
                "worker_exit_code": proc.poll() if proc is not None else job_state.get("worker_exit_code"),
                "worker_stderr_tail": _tail_text(Path(job_state.get("worker_stderr_path", "")), 8000),
            })
            _save_analysis_job_state(job_state)
            raise RuntimeError(error)
        time.sleep(0.5)


_persisted_job = _reconcile_persisted_analysis_job(_load_analysis_job_state())

st.set_page_config(page_title="Taiwan Firecloud PhysicsCore V1.0", layout="wide")
st.title("Taiwan Firecloud — PhysicsCore V1.0")
st.caption(
    f"{PROGRAM_NAME}｜版本 {__version__}｜R5.2 Finite-Solar-Disk Penumbra + Red Illumination｜基線 {__baseline__}"
)

# 僅翻譯 UI 顯示；CASE CSV 與內部欄位名稱維持英文，避免破壞既有資料相容性。
COLUMN_ZH = {
    "solar_altitude_deg": "太陽高度角 (°)",
    "time": "時間",
    "solar_azimuth_deg": "太陽方位角 (°)",
    "twilight_phase": "曙暮光階段",
    "core_score_eligible": "核心評分資格",
    "late_glow_diagnostic": "晚霞／三燒診斷",
    "physics_score": "物理潛力 (%)",
    "visual_magnitude": "視覺規模代理 (%)",
    "data_completeness": "資料完整率 (%)",
    "operational_decision": "出勤判定",
    "direction_offset_deg": "方向偏移 (°)",
    "distance_km": "距離 (km)",
    "cloud_altitude_km": "雲高 AGL (km)",
    "dynamic_rez_entry_distance_km": "動態 REZ 起始距離 (km)",
    "canvas_effective": "有效 Canvas (%)",
    "path_transmission": "光路穿透率 (%)",
    "path_completeness": "光路資料完整率 (%)",
    "rez_open_proxy": "REZ 開放代理 (%)",
    "rez_completeness": "REZ 資料完整率 (%)",
    "strong_block_proxy": "強阻光代理 (%)",
}

TEXT_ZH = {
    "HORIZON BASELINE": "地平線基準",
    "CORE / LATE-GLOW TRANSITION": "核心／晚霞交界",
    "FIRECLOUD CORE": "火燒雲核心",
    "LATE GLOW / THIRD BURN": "晚霞／三燒",
    "TWILIGHT DIAGNOSTIC": "曙暮光診斷",
    "DIAGNOSTIC ONLY": "僅供診斷",
    "GO": "可出勤",
    "CONDITIONAL GO": "條件式出勤",
    "NO-GO": "不建議出勤",
    "NO GO": "不建議出勤",
    "UNKNOWN": "未知",
    "ILLUMINATED": "受光",
    "EARTH_SHADOWED": "地球蒙影",
}


def _zh_text(v):
    if isinstance(v, str):
        return TEXT_ZH.get(v, v)
    return v


def localized_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in out.columns:
        if out[c].dtype == "object":
            out[c] = out[c].map(_zh_text)
    return out.rename(columns={c: COLUMN_ZH.get(c, c) for c in out.columns})


# V8.1.4+: session_state preserves normal reruns. V8.4.10.5 additionally
# restores the last completed result and the last interrupted request from disk.
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "analysis_request" not in st.session_state:
    st.session_state.analysis_request = None
if "recovery_loaded" not in st.session_state:
    st.session_state.recovery_loaded = False

if not st.session_state.recovery_loaded:
    if str(_persisted_job.get("status", "")).upper() == "COMPLETED" and _RESULT_STATE_PATH.exists():
        _restored = _load_completed_analysis_result()
        if _restored is not None:
            st.session_state.analysis_result = _restored
            st.session_state.analysis_request = _persisted_job.get("request") or None
    st.session_state.recovery_loaded = True

_recovery_req = (_persisted_job.get("request") or {}) if isinstance(_persisted_job, dict) else {}
try:
    _default_lat = float(_recovery_req.get("lat", 24.2500))
except Exception:
    _default_lat = 24.2500
try:
    _default_lon = float(_recovery_req.get("lon", 120.5000))
except Exception:
    _default_lon = 120.5000
try:
    _default_day = date.fromisoformat(str(_recovery_req.get("day"))) if _recovery_req.get("day") else date.today()
except Exception:
    _default_day = date.today()
_default_event = str(_recovery_req.get("event", "sunset"))

with st.sidebar:
    st.header("事件設定")
    lat = st.number_input("緯度", value=_default_lat, format="%.6f")
    lon = st.number_input("經度", value=_default_lon, format="%.6f")
    day = st.date_input("日期", value=_default_day)
    event_zh = st.selectbox("事件", ["日落", "日出"], index=1 if _default_event == "sunrise" else 0)
    event = {"日落": "sunset", "日出": "sunrise"}[event_zh]
    st.info(
        "預報資料來源：Open-Meteo 路徑／氣壓層剖面，並在可用時加入 NOAA GFS 原生雲微物理。"
        "V8.3.3 另支援具 ADS API 憑證時的 CAMS 原生 3D 氣膠消光（532 nm）＋多波長 AOD；"
        "若未設定憑證則明確標示 Missing／Unavailable，不會以固定氣膠值冒充實際資料。"
    )

    with st.expander("HITRAN 550–750 nm 六波段本地光譜", expanded=False):
        _hs = hitran_backend_status()
        if _hs.get("runtime_spectroscopy_ready", False) and _hs.get("six_band_runtime_spectroscopy_ready", False):
            st.success(
                f"READY｜LUT {_hs.get('coefficient_table_rows', 0)} 列｜來源 {_hs.get('coefficient_table_source', '')}"
            )
            _download_csv, _download_manifest = _runtime_lut_download_payloads()
            if _download_csv is not None:
                st.download_button(
                    "下載保存 Runtime LUT CSV", data=_download_csv, file_name=HITRAN_LUT_FILENAME,
                    mime="text/csv", use_container_width=True, key="hitran_runtime_download_csv_ready"
                )
                if _download_manifest is not None:
                    st.download_button(
                        "下載保存 Runtime LUT manifest", data=_download_manifest, file_name=HITRAN_MANIFEST_FILENAME,
                        mime="application/json", use_container_width=True, key="hitran_runtime_download_manifest_ready"
                    )
        else:
            st.caption(
                "正式工作流：匯入 H₂O/O₂ line lists 與 O₃ XSC → 離線建立 432-state LUT → 保存／部署 Runtime LUT。"
                "正式 Runtime 不需要 HAPI 遠端下載，也不會因 HITRAN endpoint 404 而阻塞分析。"
            )

            # V8.4.4.1: offline-first.  Remote HAPI is deliberately hidden behind an
            # explicit advanced opt-in because current transition endpoints may return 404.
            st.markdown("**① Hybrid Gas Spectroscopy 原始資料／手動匯入（正式）**")
            _legacy_db = Path(os.environ.get("FIRECLOUD_HITRAN_DB", "hitran_db")).expanduser()
            _h2o_base = _legacy_db / "H2O_535_765"
            _o2_base = _legacy_db / "O2_535_765"
            _packaged_o3_xsc_path = Path(__file__).resolve().parent / "spectroscopy_sources" / "O3_SerdyuchenkoGorshelev_213_1100nm.dat"
            _o3_xsc_path = _legacy_db / "O3_SerdyuchenkoGorshelev_213_1100nm.dat"
            _o3_xsc_ready_path = _o3_xsc_path if _o3_xsc_path.is_file() else _packaged_o3_xsc_path
            _source_rows = [
                {"氣體":"H2O", "方法":"HITRAN line-by-line + Voigt", "資料":"READY" if (_h2o_base.with_suffix(".data").is_file() and _h2o_base.with_suffix(".header").is_file()) else "MISSING"},
                {"氣體":"O2", "方法":"HITRAN line-by-line + Voigt", "資料":"READY" if (_o2_base.with_suffix(".data").is_file() and _o2_base.with_suffix(".header").is_file()) else "MISSING"},
                {"氣體":"O3", "方法":"Serdyuchenko–Gorshelev temperature-dependent XSC", "資料":"READY" if _o3_xsc_ready_path.is_file() else "MISSING"},
            ]
            st.dataframe(pd.DataFrame(_source_rows), use_container_width=True, hide_index=True)
            if _hs.get("runtime_spectroscopy_ready", False):
                st.info("現有舊 Runtime LUT 仍可讀取；但 PhysicsCore Formation 六波段要求 550/575/600/650/700/750 nm，未含 550 nm 時保持 prerequisite Missing。")
            st.caption(
                "PhysicsCore R4.8.1 採混合光譜：H₂O / O₂ 使用 HITRAN 535–765 nm 標準 .par；"
                "O₃ 使用 Serdyuchenko–Gorshelev 213–1100 nm 溫度相依 absorption cross section。"
                "O₃ 不再要求不存在的可見光 HITRAN line table。"
            )

            _line_gas = st.selectbox("匯入 HITRAN line-list 氣體", ["H2O", "O2"], key="hybrid_line_gas")
            _line_file = st.file_uploader(
                f"上傳 {_line_gas} 的 HITRAN 標準 .par / .txt",
                type=["par", "txt", "data"], key=f"hybrid_line_upload_{_line_gas}"
            )
            if st.button(f"匯入 {_line_gas} line table", disabled=_line_file is None, use_container_width=True, key=f"hybrid_import_{_line_gas}"):
                _ok_import, _import_log = _import_manual_hitran_par(_line_gas, _line_file.getvalue(), _line_file.name)
                st.session_state["hitran_manual_import_log"] = _import_log
                if _ok_import:
                    st.success(f"{_line_gas} HITRAN line table 匯入完成。")
                    st.rerun()
                else:
                    st.error(f"{_line_gas} 匯入失敗；請查看診斷紀錄。")

            _o3_file = st.file_uploader(
                "上傳 O₃ Serdyuchenko–Gorshelev XSC .dat",
                type=["dat", "txt"], key="hybrid_o3_xsc_upload"
            )
            if st.button("匯入 O₃ temperature-dependent XSC", disabled=_o3_file is None, use_container_width=True, key="hybrid_o3_xsc_import"):
                _ok_o3, _o3_log = _import_o3_serdyuchenko_xsc(_o3_file.getvalue(), _o3_file.name)
                st.session_state["hitran_o3_xsc_import_log"] = _o3_log
                if _ok_o3:
                    st.success("O₃ Serdyuchenko–Gorshelev XSC 匯入完成。")
                    st.rerun()
                else:
                    st.error("O₃ XSC 匯入失敗；請查看診斷紀錄。")

            if st.session_state.get("hitran_manual_import_log"):
                with st.expander("H₂O / O₂ HITRAN 匯入診斷", expanded=False):
                    st.code(st.session_state["hitran_manual_import_log"], language="text")
            if st.session_state.get("hitran_o3_xsc_import_log"):
                with st.expander("O₃ XSC 匯入診斷", expanded=False):
                    st.code(st.session_state["hitran_o3_xsc_import_log"], language="json")

            _hybrid_sources_ready = all(r["資料"] == "READY" for r in _source_rows)
            st.markdown("**② 增量補建 550 nm → 合併為 432-state Runtime LUT**")
            if not _hybrid_sources_ready:
                st.info("目前尚未具備 535–765 nm H₂O line table + O₂ line table + O₃ Serdyuchenko XSC；LUT 建立按鈕已停用。")
            if st.button(
                "只計算 550 nm（72 rows）並合併 432-state Runtime LUT",
                use_container_width=True,
                disabled=not _hybrid_sources_ready,
                key="hitran_lut_only",
            ):
                with st.status("PhysicsCore 550 nm 光譜建表中…", expanded=True) as _lut_status:
                    _lut_live = st.empty()
                    _lut_bar = st.progress(0.0)
                    def _lut_progress(label, elapsed, remaining):
                        _lut_live.info(f"{label}｜已執行 {elapsed:.0f} 秒｜距硬式中止最多 {remaining} 秒")
                        _lut_bar.progress(min(0.99, max(0.01, elapsed / max(1.0, elapsed + remaining))))
                    _lut_ok, _lut_log = _hitran_build_lut_only(progress_callback=_lut_progress)
                    _lut_bar.progress(1.0 if _lut_ok else 0.0)
                    st.session_state["hitran_lut_only_log"] = _lut_log
                    if _lut_ok:
                        _promote_ok, _promote_log = _promote_built_hitran_lut()
                        st.session_state["hitran_runtime_promote_log"] = _promote_log
                        if _promote_ok:
                            _lut_status.update(label="Incremental 550 nm + 432-state Runtime LUT 完成", state="complete", expanded=True)
                            st.success("HYBRID_GAS_SPECTROSCOPY = READY；正式分析只讀衍生 Runtime LUT。")
                            st.rerun()
                        else:
                            _lut_status.update(label="LUT 已建立，但 Runtime 提升失敗", state="error", expanded=True)
                            st.error("LUT build 成功，但嚴格 Runtime 驗證／安裝未通過；請查看診斷。")
                    else:
                        _lut_status.update(label="HITRAN LUT 尚未完成", state="error", expanded=True)
                        st.error("請查看 LUT 診斷紀錄。")
            if st.session_state.get("hitran_lut_only_log"):
                with st.expander("HITRAN LUT 建立診斷紀錄", expanded=False):
                    st.code(st.session_state["hitran_lut_only_log"], language="text")

            st.markdown("**③ 匯入／保存既有 Runtime LUT（跨版本沿用）**")
            st.caption(
                "這裡的 CSV / manifest 是 Taiwan Firecloud 建立後的衍生 Runtime 成品，不是 HITRAN 官網原始下載檔。"
                "第一次成功建表後請下載保存；日後換地點、換國家或升級程式都可直接沿用。"
            )
            _lut_csv_upload = st.file_uploader(
                "匯入既有 Runtime LUT CSV", type=["csv"], key="hitran_runtime_lut_csv_upload"
            )
            _lut_manifest_upload = st.file_uploader(
                "匯入 LUT manifest（建議）", type=["json"], key="hitran_runtime_manifest_upload"
            )
            if st.button(
                "驗證並安裝 Runtime LUT",
                use_container_width=True,
                disabled=_lut_csv_upload is None,
                key="hitran_runtime_install_button",
            ):
                _inst_ok, _inst_log = _install_uploaded_hitran_runtime_lut(
                    _lut_csv_upload.getvalue(),
                    _lut_manifest_upload.getvalue() if _lut_manifest_upload is not None else None,
                )
                st.session_state["hitran_runtime_install_log"] = _inst_log
                if _inst_ok:
                    st.success("Runtime LUT 驗證通過並安裝完成；HITRAN_SPECTROSCOPY 可直接 READY。")
                    st.rerun()
                else:
                    st.error("Runtime LUT 驗證失敗；未安裝。")
            if st.session_state.get("hitran_runtime_install_log"):
                with st.expander("Runtime LUT 安裝／驗證紀錄", expanded=False):
                    st.code(st.session_state["hitran_runtime_install_log"], language="json")

            _download_csv, _download_manifest = _runtime_lut_download_payloads()
            if _download_csv is not None:
                st.download_button(
                    "下載保存 Runtime LUT CSV", data=_download_csv, file_name=HITRAN_LUT_FILENAME,
                    mime="text/csv", use_container_width=True, key="hitran_runtime_download_csv"
                )
                if _download_manifest is not None:
                    st.download_button(
                        "下載保存 Runtime LUT manifest", data=_download_manifest, file_name=HITRAN_MANIFEST_FILENAME,
                        mime="application/json", use_container_width=True, key="hitran_runtime_download_manifest"
                    )

            # Historical UI labels retained for regression traceability; the new
            # extended path remains opt-in and fail-closed until its 360 states exist.
            with st.expander("進階／Legacy：HAPI 遠端自動下載（預設停用）", expanded=False):
                st.warning(
                    "目前 HITRAN transition endpoint 在實測中可能回 HTTP 404。這不是正式 Runtime 必要流程；"
                    "只有要做 endpoint 診斷時才建議啟用。"
                )
                _legacy_enable = st.checkbox(
                    "我了解此功能可能 404，仍要啟用 Legacy remote bootstrap",
                    value=False,
                    key="hitran_enable_legacy_remote",
                )
                if not _hs.get("api_key_configured", False):
                    st.info("Legacy remote bootstrap 需要 HITRAN_API_KEY；離線 Runtime LUT 匯入／使用不需要此 Key。")
                if st.button(
                    "Legacy：自動下載 line data 並建立 LUT",
                    use_container_width=True,
                    disabled=(not _legacy_enable) or (not _hs.get("api_key_configured", False)),
                    key="hitran_bootstrap_button",
                ):
                    with st.status("Legacy HITRAN 初始化中…", expanded=True) as _status:
                        _live = st.empty()
                        _bar = st.progress(0.0)
                        def _hitran_progress(label, elapsed, remaining):
                            _live.info(f"{label}｜已執行 {elapsed:.0f} 秒｜距硬式中止最多 {remaining} 秒")
                            _bar.progress(min(0.99, max(0.01, elapsed / max(1.0, elapsed + remaining))))
                        _ok, _log = _hitran_one_click_bootstrap(progress_callback=_hitran_progress)
                        _bar.progress(1.0 if _ok else 0.0)
                        st.session_state["hitran_bootstrap_log"] = _log
                        if _ok:
                            _promote_ok, _promote_log = _promote_built_hitran_lut()
                            st.session_state["hitran_runtime_promote_log"] = _promote_log
                            if _promote_ok:
                                _status.update(label="Legacy HITRAN 初始化完成並提升 Runtime LUT", state="complete", expanded=True)
                            else:
                                _status.update(label="Legacy LUT 已建立，但 Runtime 提升失敗", state="error", expanded=True)
                        else:
                            _status.update(label="Legacy HITRAN 初始化未完成", state="error", expanded=True)
                if st.session_state.get("hitran_bootstrap_log"):
                    with st.expander("Legacy HITRAN 初始化診斷紀錄", expanded=False):
                        st.code(st.session_state["hitran_bootstrap_log"], language="text")

            st.caption(
                "V8.4.16.7：550/575 nm 延伸光譜採完整 H₂O/O₂ HITRAN 535–765 nm line coverage + O₃ Serdyuchenko–Gorshelev XSC；"
                "Embedded Runtime Spectroscopy + 路徑內插效能修正。Remote HAPI 只保留手動 opt-in 建置／診斷。"
                "更換觀測地點或國家不需要重建 LUT；只有更新 spectroscopy／網格／氣體集合時才需要。"
            )

    _persisted_status = str(_persisted_job.get("status", "")).upper()
    _can_resume = _persisted_status in {"RUNNING", "INTERRUPTED", "FAILED"} and bool(_recovery_req)
    resume_run = False
    if _can_resume:
        _analysis_progress_state = {}
        _progress_path = _persisted_job.get("worker_progress_path")
        if _progress_path:
            _analysis_progress_state = _read_json_file(Path(str(_progress_path)))
        _last_message = str(
            _analysis_progress_state.get("last_message")
            or _persisted_job.get("last_message", "") or ""
        )
        _analysis_diag = ""
        if _analysis_progress_state:
            _analysis_status = str(_analysis_progress_state.get("status", "")).upper()
            try:
                _analysis_elapsed = float(_analysis_progress_state.get("elapsed_seconds", 0) or 0)
            except (TypeError, ValueError):
                _analysis_elapsed = 0.0
            _analysis_hb = str(_analysis_progress_state.get("updated_at_utc", "") or "")
            if _analysis_status in {"STARTING", "RUNNING"}:
                try:
                    _analysis_hb_dt = datetime.fromisoformat(_analysis_hb.replace("Z", "+00:00"))
                    if _analysis_hb_dt.tzinfo is None:
                        _analysis_hb_dt = _analysis_hb_dt.replace(tzinfo=timezone.utc)
                    _analysis_elapsed += max(0.0, (datetime.now(timezone.utc) - _analysis_hb_dt).total_seconds())
                except Exception:
                    pass
            _analysis_exit = _analysis_progress_state.get("exit_code", _persisted_job.get("worker_exit_code"))
            _analysis_diag = (
                f"\n\n最後分析 worker：狀態：{_analysis_status}｜"
                f"已執行：約 {_analysis_elapsed:.1f} 秒｜"
                f"PID：{_analysis_progress_state.get('worker_pid', _persisted_job.get('worker_pid', ''))}｜"
                f"Exit code：{_analysis_exit}｜最後 heartbeat：{_analysis_hb}"
            )
            _analysis_stderr = _persisted_job.get("worker_stderr_tail", "")
            if not _analysis_stderr and _persisted_job.get("worker_stderr_path"):
                _analysis_stderr = _tail_text(Path(str(_persisted_job.get("worker_stderr_path"))), 4000)
            if _analysis_stderr:
                _analysis_diag += f"\nstderr（尾端）：{_analysis_stderr[-4000:]}"
        _worker_checkpoint = _load_cams_worker_checkpoint()
        _worker_diag = ""
        if _worker_checkpoint:
            _worker_elapsed = float(_worker_checkpoint.get('elapsed_seconds', 0) or 0)
            if str(_worker_checkpoint.get('status', '')).upper() in {'STARTED', 'RUNNING', 'O3_WORKER_STARTING', 'CAMS_WORKER_STARTING'}:
                try:
                    _hb_at = datetime.fromisoformat(str(_worker_checkpoint.get('updated_at_utc', '')).replace('Z', '+00:00'))
                    if _hb_at.tzinfo is None:
                        _hb_at = _hb_at.replace(tzinfo=timezone.utc)
                    _worker_elapsed += max(0.0, (datetime.now(timezone.utc) - _hb_at).total_seconds())
                except Exception:
                    pass
            _worker_diag = (
                f"\n\n最後 CAMS worker：{_worker_checkpoint.get('role','')}｜"
                f"狀態：{_worker_checkpoint.get('status','')}｜"
                f"已執行：約 {_worker_elapsed:.1f} 秒｜"
                f"PID：{_worker_checkpoint.get('pid','')}｜"
                f"Exit code：{_worker_checkpoint.get('exit_code','')}｜"
                f"時間：{_worker_checkpoint.get('updated_at_utc','')}"
            )
            if _worker_checkpoint.get("error"):
                _worker_diag += f"\n錯誤：{_worker_checkpoint.get('error')}"
            if _worker_checkpoint.get("stderr_tail"):
                _worker_diag += f"\nstderr（尾端）：{_worker_checkpoint.get('stderr_tail')}"
        st.warning("偵測到上一次分析未正常完成。已保留事件設定與最後進度；可從既有 provider 快取重新接續。" + (f"\n\n最後進度：{_last_message}" if _last_message else "") + _analysis_diag + _worker_diag)
        resume_run = st.button("繼續上次未完成分析", type="primary", use_container_width=True, key="resume_interrupted_analysis")
    run = st.button("開始分析", type="primary", use_container_width=True) or resume_run

st.markdown(
    """
### 模型輸出層
本版本將結果分成三條輸出，不再全部壓縮成單一分數：
**物理火燒雲潛力**、**視覺規模代理**、**攝影出勤判定**。
氣壓層 cloud-cover 阻光仍保留為工程代理；當 GFS CLWMR/ICMR 可用時，另計算基於原生凝結物與假設粒徑的 COD／Beer–Lambert 微物理阻光診斷。
"""
)

if run or st.session_state.analysis_result is not None:
    if run:
        progress = st.progress(0, text="準備分析…")
        status_box = st.empty()
        _request = {
            "lat": float(lat),
            "lon": float(lon),
            "day": day.isoformat() if hasattr(day, "isoformat") else str(day),
            "event": str(event),
            "tz_name": "Asia/Taipei",
        }
        _old_job = dict(_persisted_job) if resume_run else {}
        _old_progress = _read_json_file(Path(str(_old_job.get("worker_progress_path")))) if _old_job.get("worker_progress_path") else {}
        _old_status = str(_old_progress.get("status", _old_job.get("status", ""))).upper()
        _old_pid = _old_progress.get("worker_pid", _old_job.get("worker_pid"))
        _old_alive = _pid_alive(_old_pid) if _old_pid else False
        _old_result_path = Path(str(_old_job.get("worker_result_path", ""))) if _old_job.get("worker_result_path") else None
        _analysis_proc = None
        _attach_existing = bool(
            resume_run and _old_job.get("worker_progress_path") and
            ((_old_alive and _old_status in {"STARTING", "RUNNING"}) or
             (_old_status == "COMPLETED" and _old_result_path is not None and _old_result_path.exists()))
        )
        if _attach_existing:
            # Reattach to the already detached worker.  Starting a second
            # analysis for the same recovery job would duplicate ADS requests.
            _job_state = _old_job
            _job_state.update({"status": "RUNNING", "request": _request, "version": __version__, "recovery_mode": True})
            _save_analysis_job_state(_job_state)
            _analysis_proc = None
        else:
            _job_state = {
                "job_id": str(uuid.uuid4()),
                "version": __version__,
                "status": "RUNNING",
                "request": _request,
                "progress_fraction": 0.0,
                "last_message": "準備分析…",
                "result_path": str(_RESULT_STATE_PATH),
                "recovery_mode": bool(resume_run),
            }
            _save_analysis_job_state(_job_state)
            _analysis_proc, _analysis_paths = _launch_analysis_worker(_request, _job_state)
        try:
            result = _monitor_analysis_worker(_job_state, progress, status_box, proc=_analysis_proc)
            st.session_state.analysis_result = result
            st.session_state.analysis_request = {
                "lat": float(lat),
                "lon": float(lon),
                "day": day,
                "event": str(event),
            }
            _saved = _save_completed_analysis_result(result)
            _job_state.update({
                "status": "COMPLETED",
                "worker_status": "COMPLETED",
                "progress_fraction": 1.0,
                "last_message": "分析完成",
                "result_persisted": bool(_saved),
            })
            _save_analysis_job_state(_job_state)
        except Exception as e:
            _job_state.update({
                "status": "FAILED",
                "worker_status": "FAILED",
                "last_message": f"{type(e).__name__}: {e}",
                "error_type": type(e).__name__,
                "error": str(e),
                "worker_exit_code": _analysis_proc.poll() if _analysis_proc is not None else _job_state.get("worker_exit_code"),
                "worker_stderr_tail": _tail_text(Path(str(_job_state.get("worker_stderr_path", ""))), 8000),
            })
            _save_analysis_job_state(_job_state)
            progress.empty()
            status_box.empty()
            st.error("分析未完成。事件設定與最後進度已寫入持久化恢復檔；重新載入頁面後可直接繼續上一次分析。")
            st.exception(e)
            st.stop()
        progress.progress(100, text="分析完成。")
        status_box.success("分析完成")
    else:
        result = st.session_state.analysis_result
        req = st.session_state.analysis_request or {}
        req_event_zh = {"sunset": "日落", "sunrise": "日出"}.get(req.get("event"), req.get("event", ""))
        st.info(
            f"目前顯示已完成分析：{req.get('day', '')} {req_event_zh}｜"
            f"{req.get('lat', '')}, {req.get('lon', '')}。下載或其他元件重新執行不會清除結果。"
        )

    summary = result["summary"].copy()
    for col in ["physics_score", "visual_magnitude", "data_completeness"]:
        summary[col] = (summary[col] * 100).round(1)

    st.subheader("PhysicsCore V1.0 核心形成時間軸（0°～−4°，0.5°）")
    st.caption(
        "R4 使用 0° / −0.5° / −1° / −1.5° / −2° / −2.5° / −3° / −3.5° / −4° 九個核心角度。"
        "本階段在 R3 六波段 OpticalPathResult / CloudBaseIllumination 後新增 Canvas Optical Response 與 Formation。"
        "Brightness、Redness、Effective Illuminated Area 保持分離；不產生單一 Formation Score。Viewing / Decision 尚未接入。"
    )
    _v1_summary = result.get("v1_core_summary", pd.DataFrame())
    if not _v1_summary.empty:
        _v1_show = _v1_summary.copy()
        if "cloud_geometry_completeness" in _v1_show:
            _v1_show["cloud_geometry_completeness"] = (pd.to_numeric(_v1_show["cloud_geometry_completeness"], errors="coerce")*100).round(1)
        st.dataframe(localized_df(_v1_show), use_container_width=True, hide_index=True)
    with st.expander("Legacy V8 診斷欄位（僅相容／除錯，不是 V1.0 PhysicsCore 輸出）", expanded=False):
        st.dataframe(localized_df(summary), use_container_width=True, hide_index=True)

    selected = result["selected_angle"]

    # V8.4.9.3: absence of an operational candidate must never hide the
    # diagnostic/result layers.  Pick a diagnostic display angle independently
    # from the operational selection gate so users can inspect WHY the gate
    # rejected all candidates.
    _summary_raw = result["summary"].copy()
    _core_diag = _summary_raw[_summary_raw["solar_altitude_deg"].between(-4.0, -0.5, inclusive="both")].copy()
    if selected is not None:
        diagnostic_angle = float(selected)
    elif not _core_diag.empty:
        _core_diag["_dc"] = pd.to_numeric(_core_diag.get("data_completeness"), errors="coerce").fillna(-1.0)
        _core_diag["_ps"] = pd.to_numeric(_core_diag.get("physics_score"), errors="coerce").fillna(-1.0)
        diagnostic_angle = float(_core_diag.sort_values(["_dc", "_ps", "solar_altitude_deg"], ascending=[False, False, False]).iloc[0]["solar_altitude_deg"])
    else:
        diagnostic_angle = float(_summary_raw.iloc[0]["solar_altitude_deg"])

    if selected is None:
        st.error("目前沒有任何候選時刻具備足夠有效的物理資料可供正式出勤選擇。以下仍完整顯示所有診斷、資料完整率、3D/RT 圖層與 CASE 下載，供追查缺失原因。")
        chosen = _summary_raw[_summary_raw["solar_altitude_deg"] == diagnostic_angle].iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        # Legacy regression note: older UI called this field「正式選定核心角度」;
        # R2 no longer treats that V8 selection as a PhysicsCore V1 result.
        c1.metric("V1.0 正式 Peak Window", "R4 尚未接入")
        c2.metric("診斷顯示角度", f"{diagnostic_angle:.1f}°")
        c3.metric("診斷角度資料完整率", f"{chosen['data_completeness']*100:.1f}%")
        c4.metric("Decision Layer", "R4 尚未接入")
    else:
        chosen = _summary_raw[_summary_raw["solar_altitude_deg"] == selected].iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Legacy 診斷角度", f"{selected:.1f}°")
        c2.metric("Legacy physics_score", "N/A" if pd.isna(chosen["physics_score"]) else f"{chosen['physics_score']*100:.1f}")
        c3.metric("基礎預報完整率", f"{chosen['data_completeness']*100:.1f}%")
        c4.metric("Legacy 判定（非 V1）", _zh_text(chosen["operational_decision"]))

    st.subheader("PhysicsCore V1.0-R5.2：Target Canvas Optics + Packaged Six-Band LUT")
    _v1_dep = result.get("v1_dependency_status", pd.DataFrame())
    _v1_canvas = result.get("v1_canvas_candidates", pd.DataFrame())
    _v1_sun = result.get("v1_direct_solar_fraction", pd.DataFrame())
    if not _v1_dep.empty:
        st.caption("V1.0 採 dependency-aware evidence：CAMS／O₃／Aerosol／Cloud Optics Missing 只影響依賴它的光譜路徑，不會把已知 Cloud Geometry 或 DirectSolarFraction 歸零。")
        _dshow = _v1_dep[pd.to_numeric(_v1_dep["solar_altitude_deg"], errors="coerce").eq(float(diagnostic_angle))].copy()
        st.dataframe(localized_df(_dshow), use_container_width=True, hide_index=True)
    if not _v1_canvas.empty and not _v1_sun.empty:
        _c = _v1_canvas[pd.to_numeric(_v1_canvas["solar_altitude_deg"], errors="coerce").eq(float(diagnostic_angle))].copy()
        _s = _v1_sun[pd.to_numeric(_v1_sun["solar_altitude_deg"], errors="coerce").eq(float(diagnostic_angle))].copy()
        _cs = _c.merge(_s[[c for c in ["canvas_id","direct_solar_fraction","ray_status","shadow_diagnostic_height_km"] if c in _s.columns]], on="canvas_id", how="left")
        st.dataframe(localized_df(_cs), use_container_width=True, hide_index=True)

    _r3_path = result.get("v1_spectral_optical_paths", pd.DataFrame())
    _r3_illum = result.get("v1_cloud_base_illumination", pd.DataFrame())
    _r3_hit = result.get("v1_ray_cloud_intersections", pd.DataFrame())
    if not _r3_path.empty:
        st.markdown("#### R3 六波段 Sun→CloudBase 光學路徑")
        _pshow = _r3_path[pd.to_numeric(_r3_path["solar_altitude_deg"], errors="coerce").eq(float(diagnostic_angle))].copy()
        st.caption("transmission 只有完整四成分（gas/aerosol/cloud/precip）證據時才可成為正式總傳輸；known_component_transmission 是 R3 部分證據診斷，不冒充 Full RT。")
        st.dataframe(localized_df(_pshow), use_container_width=True, hide_index=True)
    if not _r3_illum.empty:
        st.markdown("#### R3 Cloud Base Illumination")
        _ishow = _r3_illum[pd.to_numeric(_r3_illum["solar_altitude_deg"], errors="coerce").eq(float(diagnostic_angle))].copy()
        st.dataframe(localized_df(_ishow), use_container_width=True, hide_index=True)
    if not _r3_hit.empty:
        with st.expander("R3 Ray–Cloud Intersection（Native CloudScene 幾何）", expanded=False):
            _hshow = _r3_hit[pd.to_numeric(_r3_hit["solar_altitude_deg"], errors="coerce").eq(float(diagnostic_angle))].copy()
            st.dataframe(localized_df(_hshow), use_container_width=True, hide_index=True)

    _r4_canvas = result.get("v1_canvas_radiance", pd.DataFrame())
    _r4_form = result.get("v1_formation", pd.DataFrame())
    if not _r4_form.empty:
        st.markdown("#### R4 Formation（三維分量分離，不使用單一分數）")
        _fshow = _r4_form[pd.to_numeric(_r4_form["solar_altitude_deg"], errors="coerce").eq(float(diagnostic_angle))].copy()
        st.caption("R4 Tier-1 只在完整 CloudBaseIllumination + target cloud optical evidence 成立時建立六波段 Canvas response。Missing optics 會維持 UNCERTAIN，不以 Cloud Fraction/RH 假造 COT。")
        st.dataframe(localized_df(_fshow), use_container_width=True, hide_index=True)
    if not _r4_canvas.empty:
        with st.expander("R4 Canvas Radiance / Brightness / Redness / Area", expanded=False):
            _cshow = _r4_canvas[pd.to_numeric(_r4_canvas["solar_altitude_deg"], errors="coerce").eq(float(diagnostic_angle))].copy()
            st.dataframe(localized_df(_cshow), use_container_width=True, hide_index=True)

    _r44_color = result.get("v1_spectral_colour", pd.DataFrame())
    _r44_val = result.get("v1_cloud_optical_validation", pd.DataFrame())
    if not _r44_color.empty:
        with st.expander("R4.4 六波段 Spectral Color（截斷 CIE 診斷）", expanded=False):
            st.caption("只使用 550/575/600/650/700/750 nm 已有輻亮度；不補造藍／藍綠波段。XYZ/x/y 是 retained-band truncated CIE 診斷，不等同完整人眼色彩重建。")
            _x = _r44_color[pd.to_numeric(_r44_color["solar_altitude_deg"], errors="coerce").eq(float(diagnostic_angle))].copy()
            st.dataframe(localized_df(_x), use_container_width=True, hide_index=True)
    if not _r44_val.empty:
        with st.expander("R4.4 Cloud Optical Validation", expanded=False):
            _x = _r44_val[pd.to_numeric(_r44_val["solar_altitude_deg"], errors="coerce").eq(float(diagnostic_angle))].copy()
            st.dataframe(localized_df(_x), use_container_width=True, hide_index=True)

    audit = result.get("physics_data_completeness", pd.DataFrame())
    perf = result.get("performance_diagnostics", pd.DataFrame())
    if not audit.empty:
        st.subheader("Legacy V8 完整率診斷（R2 僅相容／除錯）")
        st.caption("Missing ≠ Zero ≠ Blocked。各物理層獨立判定；Full Spectral RT 只有所有必要輸入成立時才會 READY。")
        aa = audit[audit["solar_altitude_deg"] == diagnostic_angle].copy()
        layer_zh={"FORECAST_CLOUD":"基礎預報／雲場","NATIVE_AEROSOL":"Native Aerosol","O3_PROFILE":"Real O₃ Profile","GAS_PROFILE":"Gas Profile","HITRAN_SPECTROSCOPY":"HITRAN Spectroscopy","FULL_SPECTRAL_RT":"Full Spectral RT"}
        aa["診斷層"] = aa["layer"].map(layer_zh).fillna(aa["layer"])
        aa["完整率 (%)"] = (pd.to_numeric(aa["completeness"],errors="coerce")*100).round(1)
        aa=aa.rename(columns={"status":"狀態","provider":"資料來源","missing_reason":"缺失／原因"})
        st.dataframe(aa[["診斷層","狀態","完整率 (%)","資料來源","缺失／原因"]], use_container_width=True, hide_index=True)
        fr=aa[aa["診斷層"]=="Full Spectral RT"]
        if not fr.empty:
            fs=str(fr.iloc[0]["狀態"]); fc=float(fr.iloc[0]["完整率 (%)"]); reason=str(fr.iloc[0]["缺失／原因"] or "")
            if fs=="READY": st.success(f"Full Spectral RT：READY｜完整率 {fc:.1f}%")
            else: st.warning(f"Full Spectral RT：{fs}｜完整率 {fc:.1f}%" + (f"｜{reason}" if reason else ""))

    if not perf.empty:
        with st.expander("效能診斷（各太陽高度角／3D 階段）", expanded=False):
            pshow = perf.copy()
            pshow["耗時 (秒)"] = pd.to_numeric(pshow["elapsed_seconds"], errors="coerce").round(3)
            pshow = pshow.rename(columns={"solar_altitude_deg":"太陽高度角 (°)", "stage":"階段", "cache_status":"快取狀態", "cache_key":"快取鍵"})
            cols = [c for c in ["太陽高度角 (°)","階段","耗時 (秒)","快取狀態","快取鍵"] if c in pshow.columns]
            st.dataframe(pshow[cols], use_container_width=True, hide_index=True)

    st.subheader("地球蒙影 × 動態 REZ × Canvas 受光矩陣")
    st.caption(
        "純球面地球幾何。0°～−6° 的每個檢查點，都會對 2 / 4 / 5 / 8 / 12 / 18 km 雲高進行判斷。"
        "『受光』代表幾何上高於地球蒙影頂部，尚不代表雲層／氣膠光學穿透一定足夠。"
    )
    matrix_angle = st.select_slider(
        "幾何診斷太陽高度角",
        options=list(result["config"].solar_angles_deg),
        value=diagnostic_angle,
    )
    st.plotly_chart(illumination_matrix_figure(result["illumination_matrix"], matrix_angle), use_container_width=True)

    mshow = result["illumination_matrix"][result["illumination_matrix"]["solar_altitude_deg"] == matrix_angle].copy()
    mshow["geometric_state"] = mshow["geometric_state"].map(_zh_text)
    pivot = mshow.pivot(index="cloud_altitude_km", columns="distance_km", values="geometric_state")
    pivot.index.name = "雲高 AGL (km)"
    pivot.columns.name = "距離 (km)"
    st.dataframe(pivot, use_container_width=True)

    st.subheader("預報雲體 Voxel × 幾何受光")
    st.caption(
        "將實際預報雲量欄位疊合至幾何受光格點。此區仍包含較早期的 coarse voxel 診斷；"
        "缺乏垂直支援的高度保持 Missing，絕不視為 Clear。"
    )
    vc1, vc2 = st.columns(2)
    with vc1:
        voxel_direction = st.select_slider("Voxel 方向偏移", options=[-5.0, 0.0, 5.0], value=0.0)
    with vc2:
        voxel_metric_label = st.selectbox(
            "Voxel 顯示項目",
            ["有效受光雲量", "預報雲量", "上游光路穿透率", "現有雲體受光比例"],
        )
    metric_map = {
        "有效受光雲量": "effective_illuminated_cloud_proxy",
        "預報雲量": "cloud_cover_fraction",
        "上游光路穿透率": "upstream_transmission_proxy",
        "現有雲體受光比例": "illuminated_fraction_of_present_cloud_proxy",
    }
    st.plotly_chart(
        forecast_voxel_illumination_figure(
            result["forecast_voxel_matrix"], matrix_angle, voxel_direction, metric_map[voxel_metric_label]
        ),
        use_container_width=True,
    )
    vshow = result["forecast_voxel_matrix"][
        (result["forecast_voxel_matrix"]["solar_altitude_deg"] == matrix_angle)
        & (result["forecast_voxel_matrix"]["direction_offset_deg"] == voxel_direction)
    ].copy()
    vpivot = vshow.pivot(index="cloud_altitude_km", columns="distance_km", values="effective_illuminated_cloud_proxy")
    vpivot.index.name = "雲高 AGL (km)"
    vpivot.columns.name = "距離 (km)"
    st.caption("有效受光雲量代理 = 預報雲量比例 × 幾何受光狀態 × 上游雲層穿透率代理。")
    st.dataframe(vpivot, use_container_width=True)

    st.subheader("雲底／雲頂／厚度 3D Voxel 重建")
    st.caption(
        "0.5 km 垂直格點重建。較早期 low/mid/high 雲量重建仍屬 COARSE_LAYER_ENVELOPE_PROXY，"
        "不是模式原生雲底／雲頂；無垂直資料支援處保持 Missing。"
    )
    recon_label = st.selectbox(
        "重建 Voxel 顯示項目",
        ["有效受光雲體積代理", "雲體占據率代理", "幾何受光比例", "上游穿透率代理"],
    )
    recon_map = {
        "有效受光雲體積代理": "effective_illuminated_cloud_volume_proxy",
        "雲體占據率代理": "cloud_occupancy_proxy",
        "幾何受光比例": "geometric_illuminated_fraction",
        "上游穿透率代理": "upstream_transmission_proxy",
    }
    st.plotly_chart(
        reconstructed_voxel_figure(result["reconstructed_voxel_matrix"], matrix_angle, voxel_direction, recon_map[recon_label]),
        use_container_width=True,
    )
    cshow = result["reconstructed_cloud_columns"][
        (result["reconstructed_cloud_columns"]["solar_altitude_deg"] == matrix_angle)
        & (result["reconstructed_cloud_columns"]["direction_offset_deg"] == voxel_direction)
    ]
    st.dataframe(localized_df(cshow), use_container_width=True, hide_index=True)

    st.subheader("氣壓層預報 3D 雲體")
    st.caption(
        "使用氣壓層雲量、RH 與位勢高度；氣壓層以位勢高度與模式地形轉為 AGL，再插值到 0.5 km voxel。"
        "若上游模式沒有原生 Cloud Water / Ice 或 COD，程式不會自行宣稱已有真實微物理量。"
    )

    native_meta = result.get("details", {}).get(matrix_angle, {}).get("native_provider_metadata", {})
    st.subheader("GFS 原生 3D 雲微物理")
    if native_meta.get("native_status") == "FULL_NATIVE_MICROPHYSICS":
        st.success(
            f"原生 GRIB2 微物理完整｜run {native_meta.get('gfs_run_utc','')}｜"
            f"f{int(native_meta.get('gfs_forecast_hour',0)):03d}｜CLWMR + ICMR"
        )
    else:
        st.warning("GFS 原生雲微物理目前不可用；凝結物維持 Missing，絕不由 RH 人工合成。")
        if native_meta.get("native_error"):
            st.caption(native_meta.get("native_error"))

    if not result.get("native_cloud_voxel_matrix", pd.DataFrame()).empty:
        nv = result["native_cloud_voxel_matrix"]
        nsel = nv[(nv["solar_altitude_deg"] == matrix_angle) & (nv["direction_offset_deg"] == voxel_direction)] if "solar_altitude_deg" in nv.columns else nv
        if not nsel.empty:
            native_label = st.selectbox("原生 Voxel 顯示項目", ["總雲凝結物", "液態水含量", "冰水含量"], key="native_metric")
            native_metric_map = {
                "總雲凝結物": "total_cloud_condensate_kgkg",
                "液態水含量": "liquid_water_content_gm3",
                "冰水含量": "ice_water_content_gm3",
            }
            metric = native_metric_map[native_label]
            st.plotly_chart(
                reconstructed_voxel_figure(nsel.rename(columns={metric: "native_metric_value"}), matrix_angle, voxel_direction, "native_metric_value"),
                use_container_width=True,
            )

    if not result["pressure_profile_voxel_matrix"].empty:
        profile_label = st.selectbox("氣壓層 Voxel 顯示項目", ["雲體占據率", "相對濕度"], key="profile_metric")
        profile_metric = {"雲體占據率": "cloud_occupancy", "相對濕度": "relative_humidity_pct"}[profile_label]
        st.plotly_chart(
            reconstructed_voxel_figure(
                result["pressure_profile_voxel_matrix"].rename(columns={"cloud_occupancy": "cloud_occupancy_proxy"}),
                matrix_angle,
                voxel_direction,
                "cloud_occupancy_proxy" if profile_metric == "cloud_occupancy" else "relative_humidity_pct",
            ),
            use_container_width=True,
        )
        pcols = result["pressure_profile_cloud_columns"][
            (result["pressure_profile_cloud_columns"]["solar_altitude_deg"] == matrix_angle)
            & (result["pressure_profile_cloud_columns"]["direction_offset_deg"] == voxel_direction)
        ]
        st.dataframe(localized_df(pcols), use_container_width=True, hide_index=True)
    else:
        st.warning("本次分析沒有取得有效的氣壓層雲體剖面。Missing 仍保持 Missing；較早期粗略重建只作為備援診斷。")

    st.subheader("垂直雲柱光學阻擋")
    st.caption(
        "每個氣壓層雲 voxel 都可同時作為 TARGET（受光目標）與 BLOCKER（上游阻光體）。"
        "此區為 pressure-level cloud-cover 的工程代理 fallback；真正的 CLWMR/ICMR 微物理 COD 診斷顯示在下一區。"
    )
    if not result["optical_blocking_voxel_matrix"].empty:
        blocking_label = st.selectbox(
            "3D 光學顯示項目",
            ["剩餘穿透率代理", "斜向雲光學厚度代理", "有效受光雲體積代理", "幾何受光比例"],
            key="blocking_metric",
        )
        blocking_map = {
            "剩餘穿透率代理": "remaining_transmission_proxy",
            "斜向雲光學厚度代理": "slant_cloud_optical_depth_proxy",
            "有效受光雲體積代理": "effective_illuminated_cloud_volume_proxy",
            "幾何受光比例": "geometric_illuminated_fraction",
        }
        st.plotly_chart(
            reconstructed_voxel_figure(result["optical_blocking_voxel_matrix"], matrix_angle, voxel_direction, blocking_map[blocking_label]),
            use_container_width=True,
        )
        bcols = result["vertical_blocking_columns"][
            (result["vertical_blocking_columns"]["solar_altitude_deg"] == matrix_angle)
            & (result["vertical_blocking_columns"]["direction_offset_deg"] == voxel_direction)
        ]
        st.dataframe(localized_df(bcols), use_container_width=True, hide_index=True)

    st.subheader("原生 CLWMR／ICMR 雲光學厚度與阻光")
    st.caption(
        "V8.2.0 使用 GFS 原生 Cloud Liquid / Ice Mixing Ratio → LWC/IWC，並以可追溯的假設有效半徑"
        "（液滴 10 μm、冰晶 30 μm）估算可見光 extinction 與 COD，再沿 Sun→target 斜向光路累積。"
        "這是 microphysics-based COD estimate，不是模式原生／衛星反演 COT；缺少 CLWMR/ICMR 時保持 Missing。"
    )
    native_opt = result.get("native_optical_blocking_voxel_matrix", pd.DataFrame())
    if not native_opt.empty and native_opt["total_extinction_m1"].notna().any():
        native_opt_label = st.selectbox(
            "原生雲光學顯示項目",
            ["斜向累積 COD 估計", "剩餘雲層穿透率估計", "垂直 Voxel COD 估計", "總消光係數"],
            key="native_opt_metric",
        )
        native_opt_map = {
            "斜向累積 COD 估計": "slant_cloud_optical_depth_estimate",
            "剩餘雲層穿透率估計": "remaining_native_cloud_transmission_estimate",
            "垂直 Voxel COD 估計": "vertical_cloud_optical_depth_estimate",
            "總消光係數": "total_extinction_m1",
        }
        st.plotly_chart(
            reconstructed_voxel_figure(native_opt, matrix_angle, voxel_direction, native_opt_map[native_opt_label]),
            use_container_width=True,
        )
        st.caption(
            "原生雲角色診斷：`ILLUMINATED_NATIVE_CANVAS_CANDIDATE` 才是資料完整、位於受光路徑且上游光路已檢查的畫布候選；"
            "`SUNLIT_NATIVE_TARGET_PATH_UNKNOWN` 表示目標雲可見但上游阻光資料不完整；"
            "`TARGET_CONDENSATE_MISSING` 不代表晴空，`ROUTE_ENDPOINT_NO_UPSTREAM_CHECK` 不代表 100% 透光。"
        )
        ncols = result.get("native_optical_blocking_columns", pd.DataFrame())
        if not ncols.empty:
            ncols = ncols[(ncols["solar_altitude_deg"] == matrix_angle) & (ncols["direction_offset_deg"] == voxel_direction)]
            st.dataframe(localized_df(ncols), use_container_width=True, hide_index=True)
    else:
        st.warning("本次沒有可用的原生凝結物雲光學資料；程式不會以 RH 或 low/mid/high cloud cover 冒充 COD。")

    st.subheader("575–750 nm 大氣紅橙光光譜傳輸")
    st.caption(
        "V8.4.1 將 CAMS 原生 pressure-level O₃（kg/kg）與既有 T/P/RH 氣體狀態對齊，建立真實 O₃ mole fraction / number density；"
        "不使用固定 300 DU、標準 O₃ 剖面或 total-column 反推 3D profile。原生 CAMS 不可用時，O₃ 保持 Missing。"
        "只有本地 HITRAN 衍生係數與必要的 O₃/O₂/H₂O 大氣剖面都完整時才允許 Full Spectral RT；缺任何一項就保持 Missing。"
    )
    cams_status = result.get("cams_native_aerosol_provider_status", {})
    cams_rows = result.get("cams_native_aerosol_route_snapshots", pd.DataFrame())
    ozone_status = result.get("cams_native_ozone_provider_status", {})
    ozone_rows = result.get("ozone_profile_route_snapshots", pd.DataFrame())
    if not cams_rows.empty:
        st.success("本次已有 CAMS 原生 3D 氣膠資料，可優先用於 Sun→Canvas 光路積分。")
    else:
        cred = cams_status.get("credentials_configured", False)
        st.info("本次未取得 CAMS 原生 3D 氣膠資料。" + ("已偵測 ADS 憑證，請查看 CASE metadata／錯誤訊息。" if cred else "尚未設定 ADS API 憑證，因此維持 Missing／fallback 診斷。"))
    if not ozone_rows.empty and pd.to_numeric(ozone_rows.get("o3_mole_fraction", pd.Series(dtype=float)), errors="coerce").notna().any():
        o3c = pd.to_numeric(ozone_rows["o3_mole_fraction"], errors="coerce").notna().mean()*100.0
        st.success(f"Real O₃ Profile：已取得 CAMS pressure-level O₃｜有效剖面格點 {o3c:.1f}%")
    else:
        cred = ozone_status.get("credentials_configured", False)
        st.info("Real O₃ Profile：Missing。" + ("已偵測 ADS 憑證，請查看 O₃ provider metadata。" if cred else "尚未設定 ADS API 憑證；不以固定 300 DU 或人工剖面補值。"))
    hitran_status = result.get("hitran_backend_status", {}) or {}
    if hitran_status.get("runtime_spectroscopy_ready", False):
        rows = int(hitran_status.get("coefficient_table_rows", 0) or 0)
        active_wls = hitran_status.get("active_wavelengths_nm") or [600, 650, 700, 750]
        wl_label = "/".join(str(int(float(x))) for x in active_wls)
        st.success(f"HITRAN Spectroscopy：READY｜本地 {wl_label} nm LUT {rows} 列｜Runtime 不需再連線 HITRAN。")
    else:
        key_msg = "已偵測 HITRAN API Key" if hitran_status.get("api_key_configured", False) else "尚未偵測 HITRAN API Key"
        reason = str(hitran_status.get("coefficient_table_missing_reason") or hitran_status.get("gas_rt_status") or "LOCAL_HITRAN_DATA_REQUIRED")
        st.info(f"HITRAN Spectroscopy：尚未就緒｜{key_msg}｜{reason}。HITRAN line data 不隨程式包發佈；需先建立 535–765 nm 本地 line tables，再產生 PhysicsCore 六波段 LUT。")

    spectral = result.get("spectral_rt_voxel_matrix", pd.DataFrame())
    if not spectral.empty:
        spectral_angle = matrix_angle
        spectral_dir = voxel_direction
        sg = spectral[(spectral["solar_altitude_deg"] == spectral_angle) & (spectral["direction_offset_deg"] == spectral_dir)]
        _spectral_options = sorted({
            int(float(m.group(1)))
            for c in spectral.columns
            for m in [re.search(r"(?:full|partial)_spectral_transmission_(\d+)nm$", str(c))]
            if m
        }) or [600, 650, 700, 750]
        _spectral_default = 650 if 650 in _spectral_options else _spectral_options[0]
        wl = st.select_slider("光譜波長", options=_spectral_options, value=_spectral_default, key="spectral_wavelength")
        if not sg.empty:
            st.plotly_chart(
                reconstructed_voxel_figure(sg, spectral_angle, spectral_dir, f"canvas_partial_spectral_illumination_{wl}nm"),
                use_container_width=True,
            )
            show_cols=[c for c in ["distance_km","voxel_center_km",f"rayleigh_transmission_{wl}nm",f"aerosol_transmission_{wl}nm",f"cloud_transmission_{wl}nm",f"gas_transmission_{wl}nm",f"o3_transmission_{wl}nm",f"gas_tau_o3_{wl}nm",f"gas_tau_o2_{wl}nm",f"gas_tau_h2o_{wl}nm",f"partial_spectral_transmission_{wl}nm",f"full_spectral_transmission_{wl}nm",f"gas_status_{wl}nm","spectral_rt_missing_cause","spectral_rt_boundary_clipped","spectral_rt_quality"] if c in sg.columns]
            st.dataframe(localized_df(sg[show_cols]), use_container_width=True, hide_index=True)
    else:
        st.warning("本次沒有可用的 Native CLWMR/ICMR 光譜 RT 輸入；不以 RH 或雲量代理冒充完整光譜傳輸。")

    st.subheader("動態 REZ 幾何邊界")
    st.caption(
        "對每個太陽高度角與雲高，顯示朝向太陽方向第一個脫離球面地球蒙影、可獲得幾何直射光的地表距離。"
        "這是動態幾何邊界，與固定 350–440 km 的 Operational REZ 診斷帶不是同一概念。"
    )
    st.plotly_chart(dynamic_rez_figure(result["dynamic_rez"]), use_container_width=True)
    st.dataframe(localized_df(result["dynamic_rez"]), use_container_width=True, hide_index=True)

    st.subheader("方向性物理診斷")
    detail_angle = matrix_angle if matrix_angle in result.get("details", {}) else diagnostic_angle
    detail = result["details"][detail_angle]
    ddf = detail["directions"].copy()
    for col in [
        "canvas_effective",
        "path_transmission",
        "path_completeness",
        "rez_open_proxy",
        "rez_completeness",
        "strong_block_proxy",
        "physics_score",
    ]:
        if col in ddf:
            ddf[col] = (ddf[col] * 100).round(1)
    st.dataframe(localized_df(ddf), use_container_width=True, hide_index=True)

    st.subheader("太陽方向垂直剖面")
    direction = st.select_slider("方向偏移", options=[-5.0, 0.0, 5.0], value=0.0)
    fig = cross_section_figure(detail["snapshot"], direction, detail_angle, detail["voxels"])
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("路徑取樣地圖"):
        st.plotly_chart(route_map_figure(result["route_points"], lat, lon), use_container_width=True)

    with st.expander("Voxel 詳細診斷"):
        st.dataframe(localized_df(detail["voxels"]), use_container_width=True, hide_index=True)

    # CASE 封存（R2.1）：分析完成與 CASE 生成解耦。
    #
    # R2 以前會在每次 Streamlit rerun 都把所有大型 DataFrame 先 to_csv()
    # 成為完整字串，再壓進記憶體 ZIP。大型 spectral/native voxel 表可超過
    # 100 MB，這會造成顯著的額外 RAM 尖峰，看起來像「分析結束後卡住」。
    # R2.1 改為：
    #   1) 使用者按下「產生 CASE ZIP」後才序列化；
    #   2) CSV 直接串流寫入 ZipExtFile，不建立大型中間字串；
    #   3) 完成後 bytes 保存在 session_state，同一分析不重複生成；
    #   4) 顯示逐檔進度，分析畫面不再被 CASE 建檔阻塞。
    st.subheader("CASE 封存")
    st.caption(
        "分析已完成。CASE ZIP 與核心分析已解耦；只有按下「產生 CASE ZIP」後才進行大型 CSV 序列化。"
    )

    if "case_archive_bytes" not in st.session_state:
        st.session_state.case_archive_bytes = None
    if "case_archive_signature" not in st.session_state:
        st.session_state.case_archive_signature = None
    if "case_archive_elapsed" not in st.session_state:
        st.session_state.case_archive_elapsed = None

    archive_req = st.session_state.analysis_request or {"day": day, "event": event}
    archive_day = archive_req.get("day", day)
    archive_event = archive_req.get("event", event)
    _case_signature = json.dumps(
        {
            "program_version": __version__,
            "analysis_request": archive_req,
            "detail_angle": float(detail_angle) if detail_angle is not None else None,
        },
        ensure_ascii=False,
        sort_keys=True,
        default=str,
    )

    # If a new analysis / detail snapshot is active, invalidate only the old CASE
    # bytes. The physics result itself remains untouched.
    if st.session_state.case_archive_signature != _case_signature:
        st.session_state.case_archive_bytes = None
        st.session_state.case_archive_elapsed = None

    def _zip_write_csv_stream(zf, arcname, df, *, chunksize=8192):
        """Stream a DataFrame CSV directly into one ZIP member.

        This intentionally avoids ``df.to_csv()`` returning one giant Python
        string before compression.  The latter doubled/tripled peak memory for
        the 3-D/spectral matrices and could make Streamlit appear hung.
        """
        frame = df if isinstance(df, pd.DataFrame) else pd.DataFrame()
        with zf.open(arcname, mode="w") as raw:
            with io.TextIOWrapper(raw, encoding="utf-8", newline="", write_through=False) as text:
                frame.to_csv(text, index=False, chunksize=chunksize)
                text.flush()

    def _build_case_archive_bytes():
        _t0 = perf_counter()
        _mem = io.BytesIO()
        _items = [
            ("summary.csv", result["summary"]),
            ("directions.csv", detail["directions"]),
            ("voxels.csv", detail["voxels"]),
            ("route_points.csv", result["route_points"]),
            ("horizontal_sampling_profile.csv", result.get("horizontal_sampling_profile", pd.DataFrame())),
            ("illumination_matrix.csv", result["illumination_matrix"]),
            ("dynamic_rez.csv", result["dynamic_rez"]),
            ("forecast_voxel_illumination.csv", result["forecast_voxel_matrix"]),
            ("reconstructed_voxel_3d.csv", result["reconstructed_voxel_matrix"]),
            ("reconstructed_cloud_columns.csv", result["reconstructed_cloud_columns"]),
            ("pressure_profile_voxel_3d.csv", result["pressure_profile_voxel_matrix"]),
            ("pressure_profile_cloud_columns.csv", result["pressure_profile_cloud_columns"]),
            ("native_gfs_cloud_voxel_3d.csv", result["native_cloud_voxel_matrix"]),
            ("native_gfs_cloud_columns.csv", result["native_cloud_columns"]),
            ("optical_blocking_voxel_3d.csv", result["optical_blocking_voxel_matrix"]),
            ("vertical_blocking_columns.csv", result["vertical_blocking_columns"]),
            ("native_cloud_optical_blocking_voxel_3d.csv", result.get("native_optical_blocking_voxel_matrix", pd.DataFrame())),
            ("native_cloud_optical_blocking_columns.csv", result.get("native_optical_blocking_columns", pd.DataFrame())),
            ("spectral_rt_voxel_600_750nm.csv", result.get("spectral_rt_voxel_matrix", pd.DataFrame())),
            ("spectral_rt_columns_600_750nm.csv", result.get("spectral_rt_columns", pd.DataFrame())),
            ("aerosol_aod550_route_forecast.csv", result.get("aerosol_hourly_raw", pd.DataFrame())),
            ("aerosol_spectral_route_snapshots.csv", result.get("aerosol_spectral_route_snapshots", pd.DataFrame())),
            ("cams_native_aerosol_3d_route_snapshots.csv", result.get("cams_native_aerosol_route_snapshots", pd.DataFrame())),
            ("gas_profile_route_snapshots.csv", result.get("gas_profile_route_snapshots", pd.DataFrame())),
            ("ozone_profile_route_snapshots.csv", result.get("ozone_profile_route_snapshots", pd.DataFrame())),
            ("cams_grib_message_inventory.csv", result.get("cams_grib_message_inventory", pd.DataFrame())),
            ("gfs_native_request_audit.csv", result.get("gfs_native_request_audit", pd.DataFrame())),
            ("gfs_grib_message_inventory.csv", result.get("gfs_grib_message_inventory", pd.DataFrame())),
            ("gfs_native_field_completeness.csv", result.get("gfs_native_field_completeness", pd.DataFrame())),
            ("cams_request_audit.csv", result.get("cams_request_audit", pd.DataFrame())),
            ("cams_tile_audit.csv", result.get("cams_tile_audit", pd.DataFrame())),
            ("openmeteo_request_audit.csv", result.get("openmeteo_request_audit", pd.DataFrame())),
            ("openmeteo_aerosol_request_audit.csv", result.get("openmeteo_aerosol_request_audit", pd.DataFrame())),
            ("physics_data_completeness.csv", result.get("physics_data_completeness", pd.DataFrame())),
            ("v1_core_summary.csv", result.get("v1_core_summary", pd.DataFrame())),
            ("v1_cloud_layers.csv", result.get("v1_cloud_layers", pd.DataFrame())),
            ("v1_canvas_candidates.csv", result.get("v1_canvas_candidates", pd.DataFrame())),
            ("v1_direct_solar_fraction.csv", result.get("v1_direct_solar_fraction", pd.DataFrame())),
            ("v1_solar_rays.csv", result.get("v1_solar_rays", pd.DataFrame())),
            ("v1_solar_geometry.csv", result.get("v1_solar_geometry", pd.DataFrame())),
            ("v1_dependency_status.csv", result.get("v1_dependency_status", pd.DataFrame())),
            ("v1_ray_cloud_intersections.csv", result.get("v1_ray_cloud_intersections", pd.DataFrame())),
            ("v1_cloud_horizontal_support.csv", result.get("v1_cloud_horizontal_support", pd.DataFrame())),
            ("v1_native_condensate_support_diagnostics.csv", result.get("v1_native_condensate_support_diagnostics", pd.DataFrame())),
            ("v1_spectral_optical_paths_550_750nm.csv", result.get("v1_spectral_optical_paths", pd.DataFrame())),
            ("v1_cloud_base_illumination_550_750nm.csv", result.get("v1_cloud_base_illumination", pd.DataFrame())),
            ("v1_prediction_uncertainty.csv", result.get("v1_uncertainty", pd.DataFrame())),
            ("v1_optical_bottlenecks.csv", result.get("v1_optical_bottlenecks", pd.DataFrame())),
            ("v1_canvas_radiance_550_750nm.csv", result.get("v1_canvas_radiance", pd.DataFrame())),
            ("v1_formation.csv", result.get("v1_formation", pd.DataFrame())),
            ("v1_spectral_colour_550_750nm.csv", result.get("v1_spectral_colour", pd.DataFrame())),
            ("v1_cloud_optical_validation.csv", result.get("v1_cloud_optical_validation", pd.DataFrame())),
            ("v1_formation_prerequisites.csv", result.get("v1_formation_prerequisites", pd.DataFrame())),
            ("v1_precipitation_path_evidence.csv", result.get("v1_precipitation_path_evidence", pd.DataFrame())),
            ("v1_target_canvas_optical_evidence.csv", result.get("v1_target_canvas_optical_evidence", pd.DataFrame())),
            ("v1_target_canvas_optical_summary.csv", result.get("v1_target_canvas_optical_summary", pd.DataFrame())),
            ("v1_secondary_target_optics.csv", result.get("v1_secondary_target_optics", pd.DataFrame())),
            ("v1_formation_gates.csv", result.get("v1_formation_gates", pd.DataFrame())),
            ("v1_earth_shadow_penumbra_matrix.csv", result.get("v1_earth_shadow_penumbra_matrix", pd.DataFrame())),
            ("v1_canvas_penumbra_red_illumination.csv", result.get("v1_canvas_penumbra_red_illumination", pd.DataFrame())),
            ("ecmwf_ifs_request_audit.csv", result.get("ecmwf_ifs_request_audit", pd.DataFrame())),
            ("v1_six_band_spectroscopy_readiness.csv", result.get("v1_six_band_spectroscopy_readiness", pd.DataFrame())),
            ("spectral_rt_coverage_diagnostics.csv", result.get("spectral_coverage_diagnostics", pd.DataFrame())),
            (
                "spectral_rt_o3_diagnostics.csv",
                result.get("spectral_rt_voxel_matrix", pd.DataFrame()).filter(
                    regex=r"^(solar_altitude_deg|direction_offset_deg|distance_km|point_id|.*o3_.*|gas_rt_failure_cause|gas_rt_domain_status|gas_rt_expected_termination|gas_path_completeness|gas_rt_boundary_clipped)$"
                ),
            ),
            ("forecast_raw.csv", result["hourly_raw"]),
        ]
        _json_items = [
            ("native_gfs_provider_metadata.json", {str(k): v.get("native_provider_metadata", {}) for k, v in result.get("details", {}).items()}),
            ("cams_native_aerosol_provider_metadata.json", {str(k): v.get("cams_native_aerosol_metadata", {}) for k, v in result.get("details", {}).items()}),
            ("cams_native_ozone_provider_status.json", result.get("cams_native_ozone_provider_status", {})),
            ("hitran_backend_status.json", result.get("hitran_backend_status", {})),
            ("analysis_job_state.json", _load_analysis_job_state()),
            ("cams_worker_checkpoint.json", _load_cams_worker_checkpoint()),
            ("cams_worker_checkpoints.json", _load_all_cams_worker_checkpoints()),
        ]

        _total = len(_items) + len(_json_items) + 1
        _progress = st.progress(0.0, text="準備 CASE 封存…")
        _status = st.empty()
        with zipfile.ZipFile(_mem, "w", zipfile.ZIP_DEFLATED, compresslevel=1, allowZip64=True) as z:
            for _i, (_name, _df) in enumerate(_items, start=1):
                _rows = len(_df) if isinstance(_df, pd.DataFrame) else 0
                _status.caption(f"CASE：{_name}｜{_rows:,} rows")
                _zip_write_csv_stream(z, _name, _df)
                _progress.progress(_i / _total, text=f"CASE 封存 {_i}/{_total}")

            _offset = len(_items)
            for _j, (_name, _obj) in enumerate(_json_items, start=1):
                _status.caption(f"CASE：{_name}")
                z.writestr(_name, json.dumps(_obj, ensure_ascii=False, indent=2, default=str))
                _progress.progress((_offset + _j) / _total, text=f"CASE 封存 {_offset + _j}/{_total}")

            _case_export_elapsed = perf_counter() - _t0
            _perf_export = result.get("performance_diagnostics", pd.DataFrame()).copy()
            _core_rows = _perf_export[_perf_export.get("stage", pd.Series(dtype=str)).eq("TOTAL_ANALYSIS_CORE")] if not _perf_export.empty and "stage" in _perf_export.columns else pd.DataFrame()
            _core_elapsed = float(_core_rows["elapsed_seconds"].iloc[-1]) if not _core_rows.empty else float("nan")
            _extra_perf = pd.DataFrame([
                {"stage": "CASE_EXPORT_SERIALIZATION", "elapsed_seconds": _case_export_elapsed, "cache_status": "COMPUTED_STREAMING"},
                {"stage": "TOTAL_TO_CASE_ARCHIVE", "elapsed_seconds": (_core_elapsed + _case_export_elapsed) if pd.notna(_core_elapsed) else float("nan"), "cache_status": "COMPUTED_STREAMING"},
            ])
            _perf_export = pd.concat([_perf_export, _extra_perf], ignore_index=True, sort=False)
            _status.caption("CASE：performance_diagnostics.csv")
            _zip_write_csv_stream(z, "performance_diagnostics.csv", _perf_export)
            _progress.progress(1.0, text="CASE ZIP 完成")

        _elapsed = perf_counter() - _t0
        _status.empty()
        _progress.empty()
        _mem.seek(0)
        return _mem.getvalue(), _elapsed

    if st.session_state.case_archive_bytes is None:
        st.info(
            "核心分析已完成；CASE 尚未生成。這是 R2.1 的預期行為，可先查看所有分析圖表，再按下方按鈕建立封存。"
        )
        if st.button("產生 CASE ZIP", type="primary", key="build_case_zip"):
            with st.status("正在建立 CASE ZIP…", expanded=True) as _case_status:
                try:
                    _case_bytes, _case_elapsed = _build_case_archive_bytes()
                    st.session_state.case_archive_bytes = _case_bytes
                    st.session_state.case_archive_signature = _case_signature
                    st.session_state.case_archive_elapsed = _case_elapsed
                    _case_status.update(label=f"CASE ZIP 已完成（{_case_elapsed:.1f} 秒）", state="complete", expanded=False)
                except Exception as _case_exc:
                    _case_status.update(label="CASE ZIP 建立失敗", state="error", expanded=True)
                    st.exception(_case_exc)
    else:
        _elapsed = st.session_state.case_archive_elapsed
        if _elapsed is not None:
            st.success(f"CASE ZIP 已準備完成｜建立時間 {_elapsed:.1f} 秒｜同一分析不會重複序列化。")
        else:
            st.success("CASE ZIP 已準備完成。")

    if st.session_state.case_archive_bytes is not None:
        st.download_button(
            "下載本次分析 CASE ZIP",
            data=st.session_state.case_archive_bytes,
            file_name=f"Taiwan-Firecloud-PhysicsCore-V1.0-R5.2_{archive_day}_{archive_event}_CASE.zip",
            mime="application/zip",
            on_click="ignore",
            key="download_case_zip",
        )

st.divider()
st.caption(
    "重要：此版本為獨立的 PhysicsCore 參考實作。在尚未與目前正式生產分支完成合併與回歸測試前，"
    "不宣稱可直接取代現行正式版本。"
)
