import pandas as pd
import pandas.testing as pdt

from firecloud.precipitation import build_viewing_precipitation_evidence, prepare_native_hydrometeor_context
from firecloud import twilight_glow as tg


def _route():
    rows=[]
    for d in (-5.0,0.0,5.0):
        for dist in (10.0,20.0,30.0):
            r={"time":"2026-09-14T05:45:00+08:00","solar_altitude_deg":-2.0,"direction_offset_deg":d,"distance_km":dist}
            for p,z,t in ((1000,100.0,298.0),(900,1000.0,292.0),(800,2000.0,286.0),(700,3100.0,278.0)):
                r[f"geopotential_height_{p}hPa"]=z
                r[f"temperature_{p}hPa"]=t
                r[f"rain_water_kgkg_{p}hPa"]=1e-5 if p==900 else 0.0
                r[f"snow_water_kgkg_{p}hPa"]=0.0
                r[f"graupel_kgkg_{p}hPa"]=0.0
            rows.append(r)
    return pd.DataFrame(rows)


def _targets(n=6):
    rows=[]
    for i in range(n):
        rows.append({
            "time":"2026-09-14T05:45:00+08:00",
            "solar_altitude_deg":-2.0,
            "canvas_id":f"c{i}",
            "cloud_layer_id":f"c{i}",
            "direction_offset_deg":(-5.0,0.0,5.0)[i%3],
            "target_distance_km":20.0 + (i%2)*5.0,
            "target_base_km":4.0,
            "target_top_km":5.0,
            "photographic_target_eligible":True,
        })
    return pd.DataFrame(rows)


def test_prepared_viewing_precipitation_context_is_exact_equivalent():
    route=_route(); targets=_targets()
    legacy=build_viewing_precipitation_evidence(targets, route, earth_radius_km=6371.0)
    ctx=prepare_native_hydrometeor_context(route)
    prepared=build_viewing_precipitation_evidence(targets, route, earth_radius_km=6371.0, prepared_native_hydrometeor_context=ctx)
    pdt.assert_frame_equal(legacy, prepared, check_dtype=True, check_exact=True)


def test_glow_observer_precipitation_reuses_supplied_context(monkeypatch):
    route=_route(); targets=_targets()
    ctx=prepare_native_hydrometeor_context(route)
    key=("2026-09-14T05:45:00+08:00",-2.0)
    baseline=tg._observer_precipitation(targets, route, earth_radius_km=6371.0)

    def fail_prepare(*args, **kwargs):
        raise AssertionError("prepared context should prevent native hydrometeor re-preparation")

    import firecloud.precipitation as pp
    monkeypatch.setattr(pp, "_prepare_native_hydrometeor_cells", fail_prepare)
    reused=tg._observer_precipitation(targets, route, earth_radius_km=6371.0, prepared_hydrometeor_contexts={key:ctx})
    pdt.assert_frame_equal(baseline, reused, check_dtype=True, check_exact=True)


def test_prepared_viewing_precipitation_context_preserves_missing_semantics():
    route=_route(); targets=_targets()
    # One intersecting hydrometeor component is genuinely Missing. The prepared
    # path must remain fail-closed and byte/field equivalent to the legacy path.
    route.loc[(route['direction_offset_deg']==0.0) & (route['distance_km']==20.0), 'rain_water_kgkg_900hPa']=float('nan')
    legacy=build_viewing_precipitation_evidence(targets, route, earth_radius_km=6371.0)
    ctx=prepare_native_hydrometeor_context(route)
    prepared=build_viewing_precipitation_evidence(targets, route, earth_radius_km=6371.0, prepared_native_hydrometeor_context=ctx)
    pdt.assert_frame_equal(legacy, prepared, check_dtype=True, check_exact=True)


def test_prepared_viewing_precipitation_empty_route_is_exact_equivalent():
    route=pd.DataFrame(); targets=_targets(3)
    legacy=build_viewing_precipitation_evidence(targets, route, earth_radius_km=6371.0)
    ctx=prepare_native_hydrometeor_context(route)
    prepared=build_viewing_precipitation_evidence(targets, route, earth_radius_km=6371.0, prepared_native_hydrometeor_context=ctx)
    pdt.assert_frame_equal(legacy, prepared, check_dtype=True, check_exact=True)


def test_glow_runtime_stats_reports_shared_hydrometeor_context(monkeypatch):
    # Exercise only the early shared-context telemetry contract. Downstream
    # spectral/volume work is monkeypatched to empty but structurally valid
    # frames so this test cannot alter or assert science output.
    route=_route(); targets=_targets(3)
    ctx=prepare_native_hydrometeor_context(route)
    key=('2026-09-14T05:45:00+08:00',-2.0)

    geometry=pd.DataFrame({
        'time':['2026-09-14T05:45:00+08:00'],
        'solar_altitude_deg':[-2.0],
        'glow_volume_id':['g0'],
        'reference_receiver_id':['r0'],
        'direction_offset_deg':[0.0],
        'distance_km':[20.0],
        'scatter_layer_bottom_km':[4.0],
        'scatter_layer_top_km':[5.0],
        'rayleigh_phase_function_sr':[0.1],
        'glow_geometry_state':['GLOW_SCATTERING_GEOMETRY_READY'],
    })
    monkeypatch.setattr(tg,'build_twilight_glow_geometry',lambda *a,**k: geometry)
    monkeypatch.setattr(tg,'_view_targets_from_glow_geometry',lambda g: targets.iloc[[0]].copy())
    monkeypatch.setattr(tg,'_observer_precipitation',lambda *a,**k: pd.DataFrame())
    monkeypatch.setattr(tg,'build_viewing_spectral_extinction',lambda *a,**k: pd.DataFrame())
    monkeypatch.setattr(tg,'_prepare_glow_molecular_numeric_routes',lambda *a,**k: {})
    monkeypatch.setattr(tg,'summarize_twilight_glow',lambda *a,**k: pd.DataFrame())

    stats={}
    tg.build_twilight_glow_branch(
        red_light_reference=pd.DataFrame(), event_timeline=pd.DataFrame(),
        cloud_layers=pd.DataFrame(), target_optics=pd.DataFrame(),
        aerosol_snapshots=pd.DataFrame(), gas_profiles=pd.DataFrame(),
        route_snapshots=route, observer_lat_deg=23.8, observer_lon_deg=120.9,
        runtime_cache_stats=stats, viewing_runtime_context={},
        viewing_hydrometeor_contexts={key:ctx},
    )
    assert stats['viewing_hydrometeor_context_reused'] is True
    assert stats['viewing_hydrometeor_context_count'] == 1
    assert stats['viewing_hydrometeor_context_contract'] == 'R574134107_VIEWING_GLOW_NATIVE_HYDROMETEOR_CONTEXT_REUSE'
