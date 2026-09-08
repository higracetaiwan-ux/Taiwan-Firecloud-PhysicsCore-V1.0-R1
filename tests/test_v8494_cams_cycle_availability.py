from datetime import datetime, timezone

from firecloud.providers.cams_native import resolve_cams_run_and_lead


def test_before_00utc_delivery_window_uses_previous_12utc_cycle(monkeypatch):
    monkeypatch.delenv("FIRECLOUD_CAMS_AVAILABILITY_LAG_HOURS", raising=False)
    target = datetime(2026, 9, 4, 10, 10, tzinfo=timezone.utc)
    now = datetime(2026, 9, 4, 9, 31, tzinfo=timezone.utc)
    run, lead = resolve_cams_run_and_lead(target, now_utc=now)
    assert run == datetime(2026, 9, 3, 12, 0, tzinfo=timezone.utc)
    assert lead in (21, 24)


def test_just_after_nominal_delivery_window_still_uses_previous_cycle(monkeypatch):
    monkeypatch.delenv("FIRECLOUD_CAMS_AVAILABILITY_LAG_HOURS", raising=False)
    target = datetime(2026, 9, 4, 10, 30, tzinfo=timezone.utc)
    now = datetime(2026, 9, 4, 10, 30, tzinfo=timezone.utc)
    run, lead = resolve_cams_run_and_lead(target, now_utc=now)
    assert run == datetime(2026, 9, 3, 12, 0, tzinfo=timezone.utc)
    assert lead in (21, 24)


def test_after_conservative_delivery_guard_can_use_current_00utc_cycle(monkeypatch):
    monkeypatch.delenv("FIRECLOUD_CAMS_AVAILABILITY_LAG_HOURS", raising=False)
    target = datetime(2026, 9, 4, 13, 0, tzinfo=timezone.utc)
    now = datetime(2026, 9, 4, 13, 0, tzinfo=timezone.utc)
    run, lead = resolve_cams_run_and_lead(target, now_utc=now)
    assert run == datetime(2026, 9, 4, 0, 0, tzinfo=timezone.utc)
    assert lead % 3 == 0
