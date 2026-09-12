from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re

import pytest
import requests

from firecloud.providers import gfs_aws_range as a
from firecloud.providers import gfs_native as g
from firecloud.providers import gfs_canvas_optical_probe as p


class FakeResponse:
    def __init__(self, status=200, *, content=b"", text=None, headers=None):
        self.status_code = status
        self.content = content
        self._text = text
        self.headers = headers or {}
        self.closed = False

    @property
    def text(self):
        if self._text is not None:
            return self._text
        return self.content.decode("utf-8", errors="replace")

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}", response=self)

    def close(self):
        self.closed = True


class RangeSession:
    def __init__(self, idx_text, total_size=7000, range_status=206):
        self.idx_text = idx_text
        self.total_size = total_size
        self.range_status = range_status
        self.range_headers = []

    def head(self, url, **kwargs):
        return FakeResponse(200, headers={"Content-Length": str(self.total_size)})

    def get(self, url, **kwargs):
        if url.endswith(".idx"):
            return FakeResponse(200, text=self.idx_text)
        h = (kwargs.get("headers") or {}).get("Range")
        assert h and h.startswith("bytes=")
        self.range_headers.append(h)
        m = re.match(r"bytes=(\d+)-(\d*)", h)
        start = int(m.group(1)); end = int(m.group(2)) if m.group(2) else self.total_size - 1
        n = end - start + 1
        body = b"GRIB" + (b"x" * max(0, n - 8)) + b"7777"
        return FakeResponse(self.range_status, content=body)


def _idx():
    return "\n".join([
        "1:0:d=2026082918:TMP:500 mb:3 hour fcst:",
        "2:1000:d=2026082918:CLWMR:500 mb:3 hour fcst:",
        "3:2000:d=2026082918:ICMR:500 mb:3 hour fcst:",
        "4:3000:d=2026082918:UGRD:500 mb:3 hour fcst:",
        "5:4000:d=2026082918:CLWMR:700 mb:3 hour fcst:",
        "6:5000:d=2026082918:ICMR:700 mb:3 hour fcst:",
        "7:6000:d=2026082918:VGRD:700 mb:3 hour fcst:",
    ])


def test_aws_object_path_matches_gfs_v16_layout():
    run = datetime(2026, 8, 29, 18, tzinfo=timezone.utc)
    data, idx = a.build_object_urls(run, 3, "pgrb2.0p25")
    assert data.endswith("/gfs.20260829/18/atmos/gfs.t18z.pgrb2.0p25.f003")
    assert idx == data + ".idx"
    data_b, idx_b = a.build_object_urls(run, 3, "pgrb2b.0p25")
    assert data_b.endswith("gfs.t18z.pgrb2b.0p25.f003")
    assert idx_b.endswith(".idx")


def test_idx_parser_selects_only_requested_pressure_messages():
    records = a.parse_grib_index(_idx())
    assert len(records) == 7
    assert records[1].start_byte == 1000 and records[1].end_byte == 1999
    selected = a.select_pressure_messages(records, ("CLWMR", "ICMR"), (500, 700))
    assert [(r.variable, int(a._level_hpa(r.level_text))) for r in selected] == [
        ("CLWMR", 500), ("ICMR", 500), ("CLWMR", 700), ("ICMR", 700)
    ]


def test_idx_range_download_avoids_full_object_and_writes_complete_grib_spans(tmp_path, monkeypatch):
    # Force exact selected-message ranges so the expected transfer is deterministic.
    monkeypatch.setenv("FIRECLOUD_GFS_AWS_RANGE_MAX_GAP_BYTES", "0")
    session = RangeSession(_idx())
    out = tmp_path / "subset.grib2"
    meta = a.download_message_subset(
        run=datetime(2026, 8, 29, 18, tzinfo=timezone.utc), lead_hour=3,
        product="pgrb2.0p25", variables=("CLWMR", "ICMR"),
        pressure_levels_hpa=(500, 700), output_path=out, session=session,
    )
    assert out.exists()
    payload = out.read_bytes()
    assert payload.startswith(b"GRIB") and payload.endswith(b"7777")
    assert meta["selected_message_count"] == 4
    assert meta["range_request_count"] == 2
    assert meta["downloaded_bytes"] == 4000
    assert meta["full_object_size_bytes"] == 7000
    assert all(h != "bytes=0-6999" for h in session.range_headers)
    assert meta["transport"] == a.TRANSPORT_NAME


def test_range_server_returning_200_is_rejected_without_accepting_full_file(tmp_path, monkeypatch):
    monkeypatch.setenv("FIRECLOUD_GFS_AWS_RANGE_MAX_GAP_BYTES", "0")
    session = RangeSession(_idx(), range_status=200)
    with pytest.raises(RuntimeError, match="expected 206"):
        a.download_message_subset(
            run=datetime(2026, 8, 29, 18, tzinfo=timezone.utc), lead_hour=3,
            product="pgrb2.0p25", variables=("CLWMR",), pressure_levels_hpa=(500,),
            output_path=tmp_path / "bad.grib2", session=session,
        )
    assert not (tmp_path / "bad.grib2").exists()


class Nomads403Session:
    def get(self, url, **kwargs):
        return FakeResponse(403, content=b"Forbidden")


def _points():
    return [{"point_id":"P0", "distance_km":0.0, "direction_offset_deg":0.0, "lat":23.1, "lon":121.4}]


def test_primary_native_provider_falls_back_to_aws_same_frozen_run_lead(tmp_path, monkeypatch):
    monkeypatch.setattr(g, "decoder_available", lambda: True)
    monkeypatch.setattr(g, "grib_message_inventory", lambda path: [
        {"shortName":"CLWMR", "typeOfLevel":"isobaricInhPa", "level":500.0, "message_count":1},
        {"shortName":"ICMR", "typeOfLevel":"isobaricInhPa", "level":500.0, "message_count":1},
    ])
    seen = {}
    def fake_aws(**kwargs):
        seen.update(kwargs)
        Path(kwargs["output_path"]).write_bytes(b"GRIB" + b"x"*1200 + b"7777")
        return {"transport":a.TRANSPORT_NAME, "downloaded_bytes":1208, "selected_message_count":2,
                "range_request_count":2, "full_object_size_bytes":500_000_000,
                "idx_url":"https://example/index.idx", "data_url":"https://example/data"}
    monkeypatch.setattr(g, "download_aws_message_subset", fake_aws)
    valid = datetime(2026, 8, 29, 21, tzinfo=timezone.utc)
    path, meta = g.download_native_subset(_points(), valid, cache_dir=tmp_path, session=Nomads403Session())
    assert path.exists()
    assert seen["run"] == datetime(2026, 8, 29, 18, tzinfo=timezone.utc)
    assert seen["lead_hour"] == 3
    assert seen["product"] == "pgrb2.0p25"
    assert meta["gfs_run_utc"].startswith("2026-08-29T18:00:00")
    assert meta["gfs_forecast_hour"] == 3
    assert meta["gfs_historical_aws_range_fallback_used"] is True
    assert any(r.get("status") == "FAILED_NOMADS_FILTER" for r in meta["gfs_native_request_audit"])
    assert any(r.get("status") == "OK_AWS_IDX_RANGE" for r in meta["gfs_native_request_audit"])


def test_pgrb2b_probe_uses_same_aws_historical_transport_on_nomads_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(p, "decoder_available", lambda: True)
    seen = {}
    def fake_aws(**kwargs):
        seen.update(kwargs)
        Path(kwargs["output_path"]).write_bytes(b"GRIB" + b"x"*1200 + b"7777")
        return {"transport":a.TRANSPORT_NAME, "downloaded_bytes":1208, "selected_message_count":4,
                "range_request_count":2, "full_object_size_bytes":220_000_000,
                "idx_url":"https://example/b.idx", "data_url":"https://example/b"}
    monkeypatch.setattr(p, "download_aws_message_subset", fake_aws)
    valid = datetime(2026, 8, 29, 21, tzinfo=timezone.utc)
    path, meta = p.download_probe_subset(_points(), valid, cache_dir=tmp_path, session=Nomads403Session())
    assert path.exists()
    assert seen["run"] == datetime(2026, 8, 29, 18, tzinfo=timezone.utc)
    assert seen["lead_hour"] == 3
    assert seen["product"] == "pgrb2b.0p25"
    assert meta["historical_aws_range_fallback_used"] is True
    assert any(r.get("status") == "OK_AWS_IDX_RANGE" for r in meta["request_audit"])


def test_idx_selector_accepts_ncep_clmr_alias_as_native_clwmr():
    idx = "\n".join([
        "1:0:d=2026082918:CLMR:500 mb:3 hour fcst:",
        "2:1000:d=2026082918:ICMR:500 mb:3 hour fcst:",
        "3:2000:d=2026082918:CLMR:700 mb:3 hour fcst:",
        "4:3000:d=2026082918:ICMR:700 mb:3 hour fcst:",
    ])
    records = a.parse_grib_index(idx)
    selected = a.select_pressure_messages(records, ("CLWMR", "ICMR"), (500, 700))
    assert [r.variable for r in selected] == ["CLMR", "ICMR", "CLMR", "ICMR"]
    assert [a.canonical_index_variable(r.variable) for r in selected] == ["CLWMR", "ICMR", "CLWMR", "ICMR"]


def test_provider_shortname_alias_maps_clmr_to_clwmr():
    assert g._shortname("clmr") == "CLWMR"
    assert p._shortname("clmr") == "CLWMR"
