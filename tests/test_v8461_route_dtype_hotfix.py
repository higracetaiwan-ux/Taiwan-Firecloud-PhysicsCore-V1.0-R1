import pandas as pd
import numpy as np


def test_route_interpolation_promotes_integer_forecast_columns_to_float():
    from firecloud.providers.openmeteo import interpolate_route_at_time, HOURLY_VARS
    var = HOURLY_VARS[0]
    t0 = pd.Timestamp("2026-09-04 10:00:00")
    t1 = pd.Timestamp("2026-09-04 11:00:00")
    rows = []
    for pid, a, b in [("a", 1, 2), ("b", 10, 20)]:
        for t, v in [(t0, a), (t1, b)]:
            r = {"time": t, "point_id": pid, "distance_km": 0, "direction_offset_deg": 0, "lat": 0, "lon": 0}
            for c in HOURLY_VARS:
                r[c] = 0
            r[var] = v
            rows.append(r)
    df = pd.DataFrame(rows)
    assert pd.api.types.is_integer_dtype(df[var].dtype)
    out = interpolate_route_at_time(df, pd.Timestamp("2026-09-04 10:30:00").to_pydatetime())
    assert pd.api.types.is_float_dtype(out[var].dtype)
    vals = out.set_index("point_id")[var]
    assert abs(float(vals.loc["a"]) - 1.5) < 1e-12
    assert abs(float(vals.loc["b"]) - 15.0) < 1e-12
