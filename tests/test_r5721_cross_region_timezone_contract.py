from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from firecloud.solar import solar_elevation_deg, solar_azimuth_deg, find_time_for_solar_altitude
from firecloud.timezone_contract import (
    AUTO_COORDINATE, USER_OVERRIDE, coordinate_timezone, resolve_event_timezone,
)


def test_coordinate_timezone_taiwan_and_japan_regression_locations():
    tw, tw_source = coordinate_timezone(24.25, 120.5)
    jp, jp_source = coordinate_timezone(33.376, 130.31)
    assert tw == "Asia/Taipei"
    assert jp == "Asia/Tokyo"
    assert tw_source
    assert jp_source


def test_user_override_mismatch_is_preserved_and_warned_not_rewritten():
    r = resolve_event_timezone(
        33.376, 130.31, mode=USER_OVERRIDE, requested_tz_name="Asia/Taipei"
    )
    assert r.coordinate_timezone == "Asia/Tokyo"
    assert r.effective_timezone == "Asia/Taipei"
    assert r.mismatch is True
    assert "MISMATCH" in r.warning


def test_auto_coordinate_uses_coordinate_timezone():
    r = resolve_event_timezone(33.376, 130.31, mode=AUTO_COORDINATE)
    assert r.effective_timezone == "Asia/Tokyo"
    assert r.user_override_timezone == ""
    assert r.mismatch is False


def test_solar_geometry_is_invariant_to_timezone_representation_of_same_instant():
    instant_utc = datetime(2026, 9, 8, 9, 0, tzinfo=timezone.utc)
    tokyo = instant_utc.astimezone(ZoneInfo("Asia/Tokyo"))
    taipei = instant_utc.astimezone(ZoneInfo("Asia/Taipei"))

    e0 = solar_elevation_deg(33.376, 130.31, instant_utc)
    e1 = solar_elevation_deg(33.376, 130.31, tokyo)
    e2 = solar_elevation_deg(33.376, 130.31, taipei)
    a0 = solar_azimuth_deg(33.376, 130.31, instant_utc)
    a1 = solar_azimuth_deg(33.376, 130.31, tokyo)
    a2 = solar_azimuth_deg(33.376, 130.31, taipei)

    assert e0 == pytest.approx(e1, abs=1e-12)
    assert e0 == pytest.approx(e2, abs=1e-12)
    assert a0 == pytest.approx(a1, abs=1e-12)
    assert a0 == pytest.approx(a2, abs=1e-12)


def test_japan_event_local_timezone_changes_clock_label_not_physical_sunset_instant():
    d = date(2026, 9, 8)
    t_tokyo = find_time_for_solar_altitude(33.376, 130.31, d, "sunset", 0.0, "Asia/Tokyo")
    t_taipei = find_time_for_solar_altitude(33.376, 130.31, d, "sunset", 0.0, "Asia/Taipei")

    # Same physical crossing, represented one civil hour apart.
    delta_utc = abs((t_tokyo.astimezone(timezone.utc) - t_taipei.astimezone(timezone.utc)).total_seconds())
    assert delta_utc < 1.0
    assert t_tokyo.utcoffset().total_seconds() - t_taipei.utcoffset().total_seconds() == 3600
    assert t_tokyo.hour == (t_taipei.hour + 1) % 24


def test_invalid_manual_timezone_rejected():
    with pytest.raises(ValueError):
        resolve_event_timezone(33.376, 130.31, mode=USER_OVERRIDE, requested_tz_name="Not/AZone")


def test_event_time_contract_preserves_local_and_utc_evidence():
    from firecloud.timezone_contract import build_event_time_contract
    r = resolve_event_timezone(33.376, 130.31, mode=AUTO_COORDINATE)
    t = find_time_for_solar_altitude(33.376, 130.31, date(2026, 9, 8), "sunset", 0.0, r.effective_timezone)
    df = build_event_time_contract([(0.0, t, solar_azimuth_deg(33.376, 130.31, t))], r, date(2026, 9, 8), "sunset")
    assert len(df) == 1
    row = df.iloc[0]
    assert row["event_timezone"] == "Asia/Tokyo"
    assert str(row["event_local_time"]).endswith("+09:00")
    assert str(row["event_utc_time"]).endswith("+00:00")
    assert row["timezone_mode"] == AUTO_COORDINATE
    assert row["contract"] == "R5.7.21_COORDINATE_TIMEZONE_UTC_PHYSICS_V1"
