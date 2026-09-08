"""Local ephemeral per-angle DataFrame spool for PhysicsCore runtime memory control.

R5.7.24 reliability helper.  Heavy per-angle diagnostic matrices are
written to a worker-local temporary directory after each angle finishes, then
rehydrated one matrix family at a time during final aggregation.  This changes
storage scheduling only; no physical value, threshold, or scientific contract
is modified.
"""
from __future__ import annotations

from pathlib import Path
import os
import pickle
import shutil
import tempfile
from typing import Dict, Tuple

import pandas as pd


class AngleFrameSpool:
    """Disk-backed store for heavyweight per-angle DataFrames.

    Files live under the worker's local temporary filesystem rather than the
    provider-cache namespace.  They are not reusable forecast cache and are not
    valid recovery artifacts across worker processes.
    """

    def __init__(self, prefix: str = "firecloud-angle-spool-") -> None:
        self.root = Path(tempfile.mkdtemp(prefix=prefix))
        self._paths: Dict[Tuple[str, float], Path] = {}
        self.bytes_written = 0
        self.frames_written = 0

    @staticmethod
    def _safe_key(key: str) -> str:
        return "".join(c if (c.isalnum() or c in "-_") else "_" for c in str(key))

    def put(self, key: str, angle: float, frame: pd.DataFrame) -> int:
        """Persist one frame and return the serialized byte count."""
        if not isinstance(frame, pd.DataFrame) or frame.empty:
            return 0
        token = f"{float(angle):+.3f}".replace("+", "p").replace("-", "m").replace(".", "p")
        path = self.root / f"{self._safe_key(key)}__{token}.pkl"
        tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        try:
            with tmp.open("wb") as fh:
                pickle.dump(frame, fh, protocol=pickle.HIGHEST_PROTOCOL)
                fh.flush()
            os.replace(tmp, path)
        finally:
            if tmp.exists():
                try:
                    tmp.unlink()
                except Exception:
                    pass
        size = int(path.stat().st_size)
        self._paths[(str(key), float(angle))] = path
        self.bytes_written += size
        self.frames_written += 1
        return size

    def pop(self, key: str, angle: float) -> pd.DataFrame:
        """Read and delete one spooled frame; return empty if absent."""
        path = self._paths.pop((str(key), float(angle)), None)
        if path is None or not path.exists():
            return pd.DataFrame()
        try:
            with path.open("rb") as fh:
                obj = pickle.load(fh)
            return obj if isinstance(obj, pd.DataFrame) else pd.DataFrame()
        finally:
            try:
                path.unlink(missing_ok=True)
            except Exception:
                pass

    def has(self, key: str, angle: float) -> bool:
        path = self._paths.get((str(key), float(angle)))
        return bool(path is not None and path.exists())

    @property
    def pending_frames(self) -> int:
        return len(self._paths)

    def cleanup(self) -> None:
        self._paths.clear()
        try:
            shutil.rmtree(self.root, ignore_errors=True)
        except Exception:
            pass

    def __del__(self):
        try:
            self.cleanup()
        except Exception:
            pass
