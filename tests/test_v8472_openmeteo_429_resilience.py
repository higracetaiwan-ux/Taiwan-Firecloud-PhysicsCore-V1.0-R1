from types import SimpleNamespace

from firecloud.providers import openmeteo


class FakeResponse:
    def __init__(self, status_code, headers=None):
        self.status_code = status_code
        self.headers = headers or {}
    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0
    def get(self, *args, **kwargs):
        self.calls += 1
        return self.responses.pop(0)


def test_429_retry_after_then_success(monkeypatch):
    waits = []
    monkeypatch.setattr(openmeteo.time, "sleep", waits.append)
    session = FakeSession([FakeResponse(429, {"Retry-After": "3"}), FakeResponse(200)])
    r = openmeteo._get_with_rate_limit_backoff(session, "https://example.test", params={}, max_attempts=3)
    assert r.status_code == 200
    assert session.calls == 2
    assert waits == [3.0]


def test_429_without_header_uses_bounded_backoff(monkeypatch):
    waits = []
    monkeypatch.setattr(openmeteo.time, "sleep", waits.append)
    session = FakeSession([FakeResponse(429), FakeResponse(429), FakeResponse(200)])
    r = openmeteo._get_with_rate_limit_backoff(session, "https://example.test", params={}, max_attempts=4)
    assert r.status_code == 200
    assert waits == [4.0, 8.0]
