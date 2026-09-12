from __future__ import annotations

import bz2
import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from firecloud.case_archive_stream import DEFAULT_BUFFER_BYTES, write_csv_member_stream
from firecloud.providers import dwd_icon_native as icon


def _identity(run=None, lead=3, level=80, var="QC"):
    run = run or datetime(2026, 9, 12, 0, tzinfo=timezone.utc)
    url = icon._url(run, lead, level, var)
    return icon._raw_cache_identity(run, lead, level, var, url)


def test_case_csv_stream_payload_is_byte_exact_for_unicode_and_missing():
    df = pd.DataFrame({"a": [1, 2], "txt": ["高美濕地", None]})
    expected = df.to_csv(index=False).encode("utf-8")
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as zf:
        meta = write_csv_member_stream(zf, "x.csv", df, buffer_bytes=17)
    with zipfile.ZipFile(io.BytesIO(mem.getvalue())) as zf:
        actual = zf.read("x.csv")
    assert actual == expected
    assert meta["byte_size"] == len(expected)
    assert meta["sha256"] == hashlib.sha256(expected).hexdigest()


def test_case_csv_stream_default_buffer_is_4_mib():
    assert DEFAULT_BUFFER_BYTES == 4 * 1024 * 1024


def test_persistent_raw_cache_defaults_under_state_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("FIRECLOUD_STATE_DIR", str(tmp_path))
    monkeypatch.delenv("FIRECLOUD_DWD_ICON_RAW_CACHE_DIR", raising=False)
    assert icon._persistent_raw_cache_dir() == tmp_path / "provider_cache_shared" / "dwd_icon_raw"


def test_persistent_raw_cache_commit_and_validate_exact_identity(monkeypatch, tmp_path):
    monkeypatch.setenv("FIRECLOUD_STATE_DIR", str(tmp_path))
    identity = _identity()
    data, committed = icon._commit_persistent_raw_cache(identity, b"GRIB-EXACT-CONTENT")
    hit, validated = icon._validate_persistent_raw_cache(identity)
    assert hit == data
    assert committed["cache_validation_status"] == "VALID"
    assert validated["cache_validation_status"] == "VALID"
    assert validated["raw_cache_hit"] is True


def test_persistent_raw_cache_sha_corruption_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setenv("FIRECLOUD_STATE_DIR", str(tmp_path))
    identity = _identity()
    data, _ = icon._commit_persistent_raw_cache(identity, b"ORIGINAL")
    data.write_bytes(b"CORRUPTED")
    hit, meta = icon._validate_persistent_raw_cache(identity)
    assert hit is None
    assert meta["cache_validation_status"] in {"BYTE_SIZE_MISMATCH", "SHA256_MISMATCH", "QC_STAMP_MISMATCH"}


def test_persistent_raw_cache_identity_sidecar_mismatch_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setenv("FIRECLOUD_STATE_DIR", str(tmp_path))
    identity = _identity()
    data, _ = icon._commit_persistent_raw_cache(identity, b"ORIGINAL")
    _, sidecar = icon._raw_cache_paths(identity)
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    payload["identity"]["variable"] = "QI"
    sidecar.write_text(json.dumps(payload), encoding="utf-8")
    hit, meta = icon._validate_persistent_raw_cache(identity)
    assert hit is None
    assert meta["cache_validation_status"] == "IDENTITY_MISMATCH"


def test_download_decompress_uses_valid_persistent_cache_without_network(monkeypatch, tmp_path):
    monkeypatch.setenv("FIRECLOUD_STATE_DIR", str(tmp_path))
    identity = _identity()
    data, _ = icon._commit_persistent_raw_cache(identity, b"RAW-GRIB")
    monkeypatch.setattr(icon.requests, "get", lambda *a, **k: (_ for _ in ()).throw(AssertionError("network should not be used")))
    out, meta = icon._download_decompress(identity["source_url"], cache_identity=identity)
    assert out == data
    assert meta["status"] == "PERSISTENT_RAW_CACHE_HIT"
    assert meta["network_attempted"] is False
    assert meta["raw_cache_hit"] is True


def test_download_decompress_network_write_then_warm_hit(monkeypatch, tmp_path):
    monkeypatch.setenv("FIRECLOUD_STATE_DIR", str(tmp_path))
    identity = _identity()
    raw = b"GRIB-DATA-123"
    compressed = bz2.compress(raw)
    calls = {"n": 0}

    class Response:
        status_code = 200
        content = compressed

    def fake_get(*args, **kwargs):
        calls["n"] += 1
        return Response()

    monkeypatch.setattr(icon.requests, "get", fake_get)
    p1, m1 = icon._download_decompress(identity["source_url"], cache_identity=identity)
    p2, m2 = icon._download_decompress(identity["source_url"], cache_identity=identity)
    assert p1 == p2 and p1.read_bytes() == raw
    assert calls["n"] == 1
    assert m1["status"] == "DOWNLOADED" and m1["network_success"] is True
    assert m2["status"] == "PERSISTENT_RAW_CACHE_HIT" and m2["network_attempted"] is False
