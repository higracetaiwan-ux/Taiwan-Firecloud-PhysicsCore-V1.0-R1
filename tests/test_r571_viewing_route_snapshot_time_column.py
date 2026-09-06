import pandas as pd

from firecloud.providers.openmeteo import interpolate_route_at_time


def _prepare_view_snapshot_like_model(snap: pd.DataFrame, t, angle: float) -> pd.DataFrame:
    out = snap.copy()
    out["time"] = t
    if "solar_altitude_deg" in out.columns:
        out["solar_altitude_deg"] = float(angle)
    else:
        out.insert(1 if "time" in out.columns else 0, "solar_altitude_deg", float(angle))
    front = [c for c in ("time", "solar_altitude_deg") if c in out.columns]
    return out[front + [c for c in out.columns if c not in front]]


def test_r571_viewing_snapshot_does_not_reinsert_existing_time_column():
    hourly = pd.DataFrame([
        {"time": pd.Timestamp("2026-09-06 17:00:00"), "point_id": "p0", "temperature_2m": 30.0},
        {"time": pd.Timestamp("2026-09-06 18:00:00"), "point_id": "p0", "temperature_2m": 28.0},
    ])
    target = pd.Timestamp("2026-09-06 17:30:00")
    snap = interpolate_route_at_time(hourly, target.to_pydatetime())
    assert "time" in snap.columns
    out = _prepare_view_snapshot_like_model(snap, target.to_pydatetime(), -1.5)
    assert list(out.columns[:2]) == ["time", "solar_altitude_deg"]
    assert len(out) == 1
    assert float(out.loc[0, "solar_altitude_deg"]) == -1.5
