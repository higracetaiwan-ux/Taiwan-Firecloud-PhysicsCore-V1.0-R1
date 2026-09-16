import numpy as np
import pandas as pd

import firecloud.precipitation as precipitation
from firecloud.precipitation import (
    _prepare_native_hydrometeor_cells,
    _group_cells_by_horizontal_support,
    _integrate_view_path,
    build_viewing_precipitation_evidence,
)
from firecloud.shared_geometry.ray import sample_observer_los_segment, sampled_segment_path_km


def _route_native():
    rows=[]
    levels=[(1000,100,290),(950,500,288),(900,1000,285),(850,1500,282),(800,2000,280),(750,2500,276)]
    for d in (0.0,5.0,10.0,15.0):
        r={"point_id":f"+0.0_{int(d):04d}","distance_km":d,"direction_offset_deg":0.0,"precipitation":1.0}
        for p,z,t in levels:
            r[f"geopotential_height_{p}hPa"]=z
            r[f"temperature_{p}hPa"]=t
            r[f"rain_water_kgkg_{p}hPa"]=2e-4 if p in (900,850) else 0.0
            r[f"snow_water_kgkg_{p}hPa"]=1e-5 if p in (800,750) else 0.0
            r[f"graupel_kgkg_{p}hPa"]=0.0
        rows.append(r)
    return pd.DataFrame(rows)


def _target():
    return pd.DataFrame([{
        "time":"2026-09-13T10:00:00Z",
        "solar_altitude_deg":-2.0,
        "canvas_id":"glowvol::d0::10km",
        "cloud_layer_id":"glowvol::d0::10km",
        "direction_offset_deg":0.0,
        "target_distance_km":10.0,
        "target_base_km":3.5,
        "target_top_km":4.5,
        "photographic_target_eligible":True,
    }])


def _legacy_integrate_view(dt,hs,cells,earth_radius_km):
    tau=0.0; hits=0; unresolved=0; path_km=0.0
    for c in cells:
        a=max(0.0,float(c["support_start_km"])); b=min(float(dt),float(c["support_end_km"]))
        if b<=a+1e-9:
            continue
        lo=float(c["z_base_km"]); hi=float(c["z_top_km"])
        xs,zz=sample_observer_los_segment(dt,hs,a,b,sample_count=17,radius_km=earth_radius_km)
        inside=np.isfinite(zz)&(zz>=lo)&(zz<=hi)
        if not inside.any():
            continue
        hits+=1
        if not bool(c["all_hydrometeor_fields_resolved"]):
            unresolved+=1
        seg_km=sampled_segment_path_km(xs,zz,inside)
        seg=seg_km*1000.0
        if seg>0:
            path_km += seg_km
            tau += max(0.0,float(c["extinction_m1"]))*seg
    return float(tau),int(hits),int(unresolved),float(path_km)


def test_view_grouped_integrator_is_exact_legacy_equivalent():
    cells_by_dir,_=_prepare_native_hydrometeor_cells(_route_native())
    cells=cells_by_dir[0.0]
    groups=_group_cells_by_horizontal_support(cells)
    legacy=_legacy_integrate_view(10.0,4.0,cells,6371.0)
    grouped=_integrate_view_path(10.0,4.0,cells,6371.0,support_groups=groups)
    assert grouped == legacy


def test_view_grouped_integrator_samples_once_per_horizontal_support(monkeypatch):
    cells_by_dir,_=_prepare_native_hydrometeor_cells(_route_native())
    cells=cells_by_dir[0.0]
    groups=_group_cells_by_horizontal_support(cells)
    relevant=[g for g in groups if min(10.0,g[1]) > max(0.0,g[0])+1e-9]
    calls=0
    original=precipitation.sample_observer_los_segment
    def counted(*args,**kwargs):
        nonlocal calls
        calls += 1
        return original(*args,**kwargs)
    monkeypatch.setattr(precipitation,"sample_observer_los_segment",counted)
    _integrate_view_path(10.0,4.0,cells,6371.0,support_groups=groups)
    assert calls == len(relevant)
    assert calls < sum(1 for c in cells if min(10.0,float(c["support_end_km"])) > max(0.0,float(c["support_start_km"]))+1e-9)


def test_viewing_precipitation_science_dataframe_matches_legacy_values():
    snap=_route_native()
    out=build_viewing_precipitation_evidence(_target(),snap)
    cells_by_dir,_=_prepare_native_hydrometeor_cells(snap)
    cells=cells_by_dir[0.0]
    tau,hits,unresolved,path_km=_legacy_integrate_view(10.0,4.0,cells,6371.0)
    assert unresolved == 0
    assert out.loc[0,"view_precipitation_status"] == "VIEW_PRECIPITATION_OPTICS_RESOLVED"
    assert out.loc[0,"view_precipitation_intersection_count"] == hits
    assert out.loc[0,"view_precipitation_path_km"] == path_km
    for wl in (550,575,600,650,700,750):
        assert out.loc[0,f"view_tau_precip_{wl}nm"] == tau


def test_version_is_r574134103():
    import firecloud
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.20.1"

def test_view_grouped_integrator_preserves_partial_missing_intersection_semantics():
    snap=_route_native()
    snap.loc[:,"snow_water_kgkg_850hPa"]=np.nan
    cells_by_dir,_=_prepare_native_hydrometeor_cells(snap)
    cells=cells_by_dir[0.0]
    groups=_group_cells_by_horizontal_support(cells)
    legacy=_legacy_integrate_view(10.0,1.4,cells,6371.0)
    grouped=_integrate_view_path(10.0,1.4,cells,6371.0,support_groups=groups)
    assert grouped == legacy
    assert grouped[2] >= 1


def test_view_grouped_integrator_preserves_resolved_zero_when_no_layer_intersects():
    cells_by_dir,_=_prepare_native_hydrometeor_cells(_route_native())
    cells=[]
    for c in cells_by_dir[0.0]:
        q=dict(c); q["z_base_km"] += 30.0; q["z_top_km"] += 30.0; cells.append(q)
    groups=_group_cells_by_horizontal_support(cells)
    legacy=_legacy_integrate_view(10.0,4.0,cells,6371.0)
    grouped=_integrate_view_path(10.0,4.0,cells,6371.0,support_groups=groups)
    assert grouped == legacy == (0.0,0,0,0.0)
