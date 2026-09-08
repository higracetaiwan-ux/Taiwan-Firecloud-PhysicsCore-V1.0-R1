from datetime import datetime, timezone
import os

from firecloud.providers.cams_native import resolve_cams_run_and_lead
from firecloud.providers.gfs_native import resolve_run_and_lead


def dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace('Z', '+00:00'))


def test_cams_frozen_analysis_clock_prevents_boundary_drift(monkeypatch):
    target = dt('2026-09-08T10:06:52+00:00')
    monkeypatch.setenv('FIRECLOUD_PROVIDER_RESOLUTION_NOW_UTC', '2026-09-08T12:07:00+00:00')
    run, lead = resolve_cams_run_and_lead(target)
    assert run == dt('2026-09-07T12:00:00+00:00')
    assert lead == 21


def test_cams_explicit_now_still_overrides_frozen_environment(monkeypatch):
    target = dt('2026-09-08T10:06:52+00:00')
    monkeypatch.setenv('FIRECLOUD_PROVIDER_RESOLUTION_NOW_UTC', '2026-09-08T12:07:00+00:00')
    run, lead = resolve_cams_run_and_lead(target, now_utc=dt('2026-09-08T12:16:00+00:00'))
    assert run == dt('2026-09-08T00:00:00+00:00')
    assert lead == 9


def test_cams_all_event_times_keep_same_frozen_cycle_across_long_job(monkeypatch):
    monkeypatch.setenv('FIRECLOUD_PROVIDER_RESOLUTION_NOW_UTC', '2026-09-08T12:07:00+00:00')
    targets = [dt('2026-09-08T10:06:52+00:00'), dt('2026-09-08T10:33:26+00:00')]
    resolved = [resolve_cams_run_and_lead(t) for t in targets]
    assert [x[0] for x in resolved] == [dt('2026-09-07T12:00:00+00:00')]*2
    assert [x[1] for x in resolved] == [21, 24]


def test_gfs_uses_same_analysis_clock_freeze(monkeypatch):
    # At 17:01 UTC the nominal 12Z+5h cycle becomes available. A job that
    # started at 16:59 must continue using the same 06Z cycle throughout.
    target = dt('2026-09-08T20:00:00+00:00')
    monkeypatch.setenv('FIRECLOUD_PROVIDER_RESOLUTION_NOW_UTC', '2026-09-08T16:59:00+00:00')
    run, lead = resolve_run_and_lead(target)
    assert run == dt('2026-09-08T06:00:00+00:00')
    assert lead == 15
    run2, lead2 = resolve_run_and_lead(target, now_utc=dt('2026-09-08T17:01:00+00:00'))
    assert run2 == dt('2026-09-08T12:00:00+00:00')
    assert lead2 == 9
