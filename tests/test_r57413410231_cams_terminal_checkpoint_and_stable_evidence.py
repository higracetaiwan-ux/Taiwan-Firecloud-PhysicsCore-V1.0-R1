from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from firecloud.providers import cams_native
from firecloud import ice_microphysics_wyser_yang_diagnostic_bulk_integration as bulk


def _points():
    return [
        {
            "point_id": "p0",
            "lat": 25.0,
            "lon": 121.0,
            "distance_km": 0.0,
            "direction_offset_deg": 0.0,
        }
    ]


def test_timeout_deferred_child_result_reconciles_durable_checkpoint(monkeypatch, tmp_path):
    state_dir = tmp_path / "state"
    monkeypatch.setenv("FIRECLOUD_STATE_DIR", str(state_dir))
    monkeypatch.setattr(cams_native, "_load_decoded_role_cache", lambda *a, **k: None)
    monkeypatch.setattr(cams_native, "_save_decoded_role_cache", lambda *a, **k: {"status": "SKIPPED", "elapsed_seconds": 0.0})

    class FakePopen:
        def __init__(self, cmd, **kwargs):
            self.pid = 4242
            self.returncode = 1
            result_path = Path(cmd[-1])
            cams_native._write_cams_worker_result(
                result_path,
                {
                    "role": "PRESSURE_LEVEL_CHEMISTRY_OPTICS_BUNDLE",
                    "status": "TIMEOUT_DEFERRED",
                    "df": pd.DataFrame(),
                    "meta": {
                        "request_audit": {
                            "request_role": "PRESSURE_LEVEL_CHEMISTRY_OPTICS_BUNDLE",
                            "status": "TIMEOUT_DEFERRED",
                            "final_status": "TIMEOUT_DEFERRED",
                        }
                    },
                    "inventory": [],
                    "error": "CAMS_ADS_QUEUE_GRACE_EXCEEDED",
                },
            )

        def poll(self):
            return self.returncode

        def terminate(self):
            self.returncode = -15

        def kill(self):
            self.returncode = -9

        def wait(self, timeout=None):
            return self.returncode

    monkeypatch.setattr(cams_native.subprocess, "Popen", FakePopen)

    result = cams_native._run_cams_role_isolated(
        "PRESSURE_LEVEL_CHEMISTRY_OPTICS_BUNDLE",
        _points(),
        datetime(2026, 9, 17, 0, tzinfo=timezone.utc),
        cache_dir=tmp_path / "cache",
        deadline_seconds=5.0,
    )

    assert result["status"] == "TIMEOUT_DEFERRED"
    checkpoint = pd.read_json(state_dir / "cams_worker_checkpoint.json", typ="series")
    assert checkpoint["role"] == "PRESSURE_LEVEL_CHEMISTRY_OPTICS_BUNDLE"
    assert checkpoint["status"] == "TIMEOUT_DEFERRED"
    assert checkpoint["exit_code"] == 1
    assert checkpoint["error"] == "CAMS_ADS_QUEUE_GRACE_EXCEEDED"


def test_step3j_evidence_float_serialization_collapses_one_ulp_noise():
    a = 35.736078690506133
    b = 35.736078690506126
    assert a != b
    assert hasattr(bulk, "stable_evidence_float")
    assert bulk.stable_evidence_float(a) == bulk.stable_evidence_float(b)
    assert bulk.stable_evidence_float(a) == "35.73607869050613"
