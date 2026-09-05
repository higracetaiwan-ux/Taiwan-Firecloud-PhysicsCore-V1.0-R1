from datetime import datetime
import math

import requests

from firecloud.providers import openmeteo


class Resp429:
    status_code = 429
    headers = {}
    def raise_for_status(self):
        raise requests.HTTPError("HTTP 429")


class RateLimitedSession:
    calls = 0
    def get(self, *args, **kwargs):
        type(self).calls += 1
        return Resp429()


def _point(i):
    return {
        "point_id": f"0_{i:03d}",
        "lat": 24.0 + i * 0.01,
        "lon": 121.0 + i * 0.01,
        "distance_km": float(i * 20),
        "direction_offset_deg": 0.0,
    }


def test_terminal_429_opens_circuit_and_preserves_missing_route(monkeypatch, tmp_path):
    monkeypatch.setenv("FIRECLOUD_OPENMETEO_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("FIRECLOUD_OPENMETEO_MAX_ATTEMPTS", "2")
    monkeypatch.setattr(openmeteo.requests, "Session", RateLimitedSession)
    monkeypatch.setattr(openmeteo.time, "sleep", lambda *_: None)
    RateLimitedSession.calls = 0

    # 31 unique points -> three provider batches at batch_size=15.
    pts = [_point(i) for i in range(31)]
    out = openmeteo.fetch_route_hourly(
        pts, datetime(2026, 9, 4), datetime(2026, 9, 4)
    )

    # Only the first cache-miss batch is retried. Remaining misses are skipped
    # after the 429 circuit opens, so a single analysis cannot hammer the API.
    assert RateLimitedSession.calls == 2
    assert out.attrs["rate_limit_deferred"] is True
    assert out.attrs["openmeteo_status"] == "PARTIAL_RATE_LIMIT"
    assert out["point_id"].nunique() == 31
    assert len(out) == 31 * 24
    assert out["cloud_cover_low"].isna().all()

    audit = out.attrs["api_request_audit"]
    assert audit[0]["network_status"] == "RATE_LIMIT_DEFERRED"
    assert audit[1]["network_status"] == "SKIPPED_RATE_LIMIT_CIRCUIT_OPEN"
    assert audit[2]["network_status"] == "SKIPPED_RATE_LIMIT_CIRCUIT_OPEN"


def test_429_exception_is_distinct_from_other_http_errors(monkeypatch):
    monkeypatch.setattr(openmeteo.time, "sleep", lambda *_: None)
    class S:
        def get(self, *a, **k):
            return Resp429()
    try:
        openmeteo._get_with_rate_limit_backoff(S(), "https://example.test", params={}, max_attempts=1)
    except openmeteo.OpenMeteoRateLimitError as exc:
        assert exc.response.status_code == 429
    else:
        raise AssertionError("expected OpenMeteoRateLimitError")
