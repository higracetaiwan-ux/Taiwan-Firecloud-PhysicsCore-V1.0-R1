"""Coordinate-aware timezone contract for PhysicsCore event analysis.

R5.7.21 goals:
- event dates are interpreted in an explicit local civil timezone;
- all physical solar/forecast instants remain timezone-aware and are canonicalized to UTC;
- coordinate resolution is provenance-bearing and deterministic;
- user overrides are never silently rewritten;
- resolver failure degrades to a fixed-offset timezone rather than Asia/Taipei.

The optional :mod:`timezonefinder` dependency provides global IANA lookup.  A
small deterministic fallback covers the project's Taiwan/Japan regression
locations and otherwise uses an ``Etc/GMT`` fixed-offset zone derived from
longitude.  The fallback is diagnostic and does not claim political timezone
boundary accuracy or daylight-saving support.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import math

import pandas as pd

AUTO_COORDINATE = "AUTO_COORDINATE"
USER_OVERRIDE = "USER_OVERRIDE"


@dataclass(frozen=True)
class TimezoneResolution:
    lat: float
    lon: float
    mode: str
    coordinate_timezone: str
    effective_timezone: str
    resolver_source: str
    user_override_timezone: str
    mismatch: bool
    warning: str

    def to_dict(self) -> dict:
        return asdict(self)


def _valid_iana(name: str | None) -> bool:
    if not name:
        return False
    try:
        ZoneInfo(str(name))
        return True
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        return False


def _fixed_offset_from_longitude(lon: float) -> str:
    # Civil-time fallback only. Round to nearest nominal 15-degree meridian.
    offset = int(max(-12, min(14, round(float(lon) / 15.0))))
    if offset == 0:
        return "Etc/GMT"
    # IANA Etc/GMT sign is intentionally reversed.
    return f"Etc/GMT{'-' if offset > 0 else '+'}{abs(offset)}"


def _regional_fallback(lat: float, lon: float) -> tuple[str | None, str | None]:
    lat = float(lat); lon = float(lon)
    # Taiwan and immediate offshore islands used by the operational project.
    if 21.5 <= lat <= 26.5 and 118.0 <= lon <= 123.5:
        return "Asia/Taipei", "REGIONAL_FALLBACK_TAIWAN"
    # Kyushu / western Japan regression area, including the user's 33.376,130.31 case.
    if 29.0 <= lat <= 36.0 and 128.0 <= lon <= 134.5:
        return "Asia/Tokyo", "REGIONAL_FALLBACK_WESTERN_JAPAN"
    # Okinawa / Ryukyu chain.
    if 23.0 <= lat <= 29.5 and 122.0 <= lon <= 131.5:
        return "Asia/Tokyo", "REGIONAL_FALLBACK_RYUKYU"
    return None, None


_TIMEZONE_FINDER = None
_TIMEZONE_FINDER_INIT_ATTEMPTED = False


def _timezonefinder_lookup(lat: float, lon: float) -> str | None:
    global _TIMEZONE_FINDER, _TIMEZONE_FINDER_INIT_ATTEMPTED
    if not _TIMEZONE_FINDER_INIT_ATTEMPTED:
        _TIMEZONE_FINDER_INIT_ATTEMPTED = True
        try:
            from timezonefinder import TimezoneFinder  # type: ignore
            try:
                _TIMEZONE_FINDER = TimezoneFinder(in_memory=True)
            except TypeError:
                _TIMEZONE_FINDER = TimezoneFinder()
        except Exception:
            _TIMEZONE_FINDER = None
    if _TIMEZONE_FINDER is None:
        return None
    try:
        name = _TIMEZONE_FINDER.timezone_at(lat=float(lat), lng=float(lon))
        return str(name) if name and _valid_iana(str(name)) else None
    except Exception:
        return None


def coordinate_timezone(lat: float, lon: float) -> tuple[str, str]:
    """Resolve coordinates to an IANA timezone plus resolver provenance."""
    lat = float(lat); lon = float(lon)
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
        raise ValueError("Latitude/longitude outside valid range")

    name = _timezonefinder_lookup(lat, lon)
    if name:
        return name, "TIMEZONEFINDER"

    name, source = _regional_fallback(lat, lon)
    if name and _valid_iana(name):
        return name, str(source)

    fixed = _fixed_offset_from_longitude(lon)
    if _valid_iana(fixed):
        return fixed, "LONGITUDE_FIXED_OFFSET_FALLBACK"
    return "UTC", "UTC_LAST_RESORT"


def resolve_event_timezone(
    lat: float,
    lon: float,
    *,
    mode: str = AUTO_COORDINATE,
    requested_tz_name: str | None = None,
) -> TimezoneResolution:
    coordinate_tz, source = coordinate_timezone(lat, lon)
    mode_norm = str(mode or AUTO_COORDINATE).upper()
    requested = str(requested_tz_name or "").strip()

    if mode_norm == USER_OVERRIDE:
        if not _valid_iana(requested):
            raise ValueError(f"Invalid user timezone override: {requested or '<empty>'}")
        mismatch = requested != coordinate_tz
        warning = (
            f"USER_TIMEZONE_OVERRIDE_MISMATCH: coordinate resolver={coordinate_tz}, override={requested}; "
            "the override is preserved and not silently rewritten."
            if mismatch else ""
        )
        effective = requested
    else:
        mode_norm = AUTO_COORDINATE
        mismatch = False
        warning = ""
        effective = coordinate_tz
        requested = ""

    return TimezoneResolution(
        lat=float(lat), lon=float(lon), mode=mode_norm,
        coordinate_timezone=coordinate_tz,
        effective_timezone=effective,
        resolver_source=source,
        user_override_timezone=requested,
        mismatch=bool(mismatch), warning=warning,
    )


def utc_iso(when: datetime) -> str:
    if when.tzinfo is None:
        raise ValueError("UTC conversion requires timezone-aware datetime")
    return when.astimezone(timezone.utc).isoformat()


def utc_offset_hours(tz_name: str, when_local: datetime) -> float:
    if when_local.tzinfo is None:
        when_local = when_local.replace(tzinfo=ZoneInfo(tz_name))
    off = when_local.utcoffset()
    return float(off.total_seconds() / 3600.0) if off is not None else math.nan


def build_event_time_contract(
    candidates,
    resolution: TimezoneResolution,
    day: date,
    event: str,
) -> pd.DataFrame:
    """Build stable CASE evidence for local-civil vs UTC event instants."""
    rows = []
    for angle, when_local, _azimuth in candidates:
        if when_local.tzinfo is None:
            raise ValueError("Event timeline contains naive datetime")
        rows.append({
            "solar_altitude_deg": float(angle),
            "event_local_time": when_local.isoformat(),
            "event_utc_time": utc_iso(when_local),
            "event_timezone": resolution.effective_timezone,
            "utc_offset_hours": utc_offset_hours(resolution.effective_timezone, when_local),
            "timezone_mode": resolution.mode,
            "coordinate_timezone": resolution.coordinate_timezone,
            "timezone_resolver_source": resolution.resolver_source,
            "timezone_override": resolution.user_override_timezone,
            "timezone_mismatch": bool(resolution.mismatch),
            "timezone_warning": resolution.warning,
            "event_local_date": day.isoformat(),
            "event_kind": str(event),
            "contract": "R5.7.21_COORDINATE_TIMEZONE_UTC_PHYSICS_V1",
        })
    return pd.DataFrame(rows, columns=[
        "solar_altitude_deg", "event_local_time", "event_utc_time", "event_timezone",
        "utc_offset_hours", "timezone_mode", "coordinate_timezone",
        "timezone_resolver_source", "timezone_override", "timezone_mismatch",
        "timezone_warning", "event_local_date", "event_kind", "contract",
    ])
