import pandas as pd

from firecloud.precipitation import (
    build_precipitation_path_evidence,
    prepare_native_hydrometeor_context,
)


class C:
    canvas_id = "canvas::dir+0.0_d5.0_L1"
    cloud_layer_id = "dir+0.0_d5.0_L1"
    distance_km = 5.0
    cloud_base_altitude_km = 2.0


def _route_native():
    rows = []
    for d in (0.0, 5.0, 10.0):
        r = {"point_id": f"+0.0_{int(d):04d}", "distance_km": d, "direction_offset_deg": 0.0, "precipitation": 1.0}
        for p, z, t in [(1000, 100, 290), (900, 1000, 285), (800, 2000, 280)]:
            r[f"geopotential_height_{p}hPa"] = z
            r[f"temperature_{p}hPa"] = t
            r[f"rain_water_kgkg_{p}hPa"] = 2e-4 if p == 900 else 0.0
            r[f"snow_water_kgkg_{p}hPa"] = 0.0
            r[f"graupel_kgkg_{p}hPa"] = 0.0
        rows.append(r)
    return pd.DataFrame(rows)


def test_prepared_native_hydrometeor_context_is_exact_equivalent():
    snap = _route_native()
    baseline = build_precipitation_path_evidence([C()], snap, solar_altitude_deg=-2.0)
    context = prepare_native_hydrometeor_context(snap)
    reused = build_precipitation_path_evidence(
        [C()], snap, solar_altitude_deg=-2.0,
        prepared_native_hydrometeor_context=context,
    )
    pd.testing.assert_frame_equal(reused, baseline, check_dtype=True, check_exact=True)


def test_model_has_cross_angle_red_light_precipitation_context_cache():
    import firecloud.model as model
    text = open(model.__file__, encoding="utf-8").read()
    assert "precipitation_native_context_cache = {}" in text
    assert 'stage": "RED_LIGHT_PRECIPITATION_NATIVE_CONTEXT"' in text
    assert "R57413491_EXACT_REUSE_SAME_FORECAST_SNAPSHOT" in text
