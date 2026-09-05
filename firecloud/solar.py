from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
import math


def _fractional_year(when: datetime) -> float:
    doy = when.timetuple().tm_yday
    hour = when.hour + when.minute / 60 + when.second / 3600
    days = 366 if (when.year % 4 == 0 and (when.year % 100 != 0 or when.year % 400 == 0)) else 365
    return 2.0 * math.pi / days * (doy - 1 + (hour - 12.0) / 24.0)


def _eqtime_declination(when: datetime) -> tuple[float, float]:
    """NOAA solar approximation: equation of time (min), declination (rad)."""
    g = _fractional_year(when)
    eqtime = 229.18 * (
        0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g)
        - 0.014615 * math.cos(2*g) - 0.040849 * math.sin(2*g)
    )
    decl = (
        0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g)
        - 0.006758 * math.cos(2*g) + 0.000907 * math.sin(2*g)
        - 0.002697 * math.cos(3*g) + 0.00148 * math.sin(3*g)
    )
    return eqtime, decl


def _solar_geometry(lat: float, lon: float, when: datetime) -> tuple[float, float]:
    if when.tzinfo is None:
        raise ValueError("Solar calculations require a timezone-aware datetime")
    eqtime, decl = _eqtime_declination(when)
    offset_hours = when.utcoffset().total_seconds() / 3600.0
    minutes = when.hour * 60 + when.minute + when.second / 60 + when.microsecond / 60_000_000
    true_solar_time = (minutes + eqtime + 4.0 * lon - 60.0 * offset_hours) % 1440.0
    hour_angle_deg = true_solar_time / 4.0 - 180.0
    if hour_angle_deg < -180:
        hour_angle_deg += 360.0

    lat_r = math.radians(lat)
    ha = math.radians(hour_angle_deg)
    cos_zen = math.sin(lat_r) * math.sin(decl) + math.cos(lat_r) * math.cos(decl) * math.cos(ha)
    cos_zen = max(-1.0, min(1.0, cos_zen))
    zen = math.acos(cos_zen)
    elevation = 90.0 - math.degrees(zen)  # geometric, no atmospheric refraction

    # NOAA convention: clockwise from North.
    az = math.degrees(math.atan2(
        math.sin(ha),
        math.cos(ha) * math.sin(lat_r) - math.tan(decl) * math.cos(lat_r)
    )) + 180.0
    az %= 360.0
    return elevation, az


def solar_elevation_deg(lat: float, lon: float, when: datetime) -> float:
    return _solar_geometry(lat, lon, when)[0]


def solar_azimuth_deg(lat: float, lon: float, when: datetime) -> float:
    return _solar_geometry(lat, lon, when)[1]


def _bisect_altitude(lat: float, lon: float, lo: datetime, hi: datetime, target: float) -> datetime:
    f_lo = solar_elevation_deg(lat, lon, lo) - target
    f_hi = solar_elevation_deg(lat, lon, hi) - target
    if f_lo * f_hi > 0:
        return lo if abs(f_lo) < abs(f_hi) else hi
    for _ in range(50):
        mid = lo + (hi - lo) / 2
        f_mid = solar_elevation_deg(lat, lon, mid) - target
        if abs(f_mid) < 1e-6:
            return mid
        if f_lo * f_mid <= 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return lo + (hi - lo) / 2


def _crossings_for_altitude(lat: float, lon: float, day: date, target: float, tz_name: str) -> list[tuple[datetime, str]]:
    tz = ZoneInfo(tz_name)
    start = datetime.combine(day, time(0, 0), tz)
    step = timedelta(minutes=5)
    out = []
    prev_t = start
    prev_v = solar_elevation_deg(lat, lon, prev_t) - target
    for i in range(1, 289):
        t = start + i * step
        v = solar_elevation_deg(lat, lon, t) - target
        if prev_v == 0 or v == 0 or prev_v * v < 0:
            root = _bisect_altitude(lat, lon, prev_t, t, target)
            before = solar_elevation_deg(lat, lon, root - timedelta(seconds=30))
            after = solar_elevation_deg(lat, lon, root + timedelta(seconds=30))
            kind = "sunrise" if after > before else "sunset"
            if not out or abs((root - out[-1][0]).total_seconds()) > 60:
                out.append((root, kind))
        prev_t, prev_v = t, v
    return out


def event_time(lat: float, lon: float, day: date, event: str, tz_name: str = "Asia/Taipei") -> datetime:
    matches = [t for t, kind in _crossings_for_altitude(lat, lon, day, 0.0, tz_name) if kind == event]
    if not matches:
        raise ValueError(f"No {event} geometric-horizon crossing found for {day} at this location")
    return matches[0]


def find_time_for_solar_altitude(
    lat: float,
    lon: float,
    day: date,
    event: str,
    target_altitude_deg: float,
    tz_name: str = "Asia/Taipei",
) -> datetime:
    matches = [t for t, kind in _crossings_for_altitude(lat, lon, day, target_altitude_deg, tz_name) if kind == event]
    if matches:
        return matches[0]
    # Fallback near geometric sunrise/sunset.
    base = event_time(lat, lon, day, event, tz_name)
    best_t, best_err = base, float("inf")
    for i in range(-90, 91):
        t = base + timedelta(minutes=i)
        err = abs(solar_elevation_deg(lat, lon, t) - target_altitude_deg)
        if err < best_err:
            best_t, best_err = t, err
    return best_t
