import math
import numpy as np
import pandas as pd

import firecloud.precipitation as precipitation
from firecloud.precipitation import (
    _prepare_native_hydrometeor_cells,
    _group_cells_by_horizontal_support,
    _integrate_sun_path,
    build_precipitation_path_evidence,
    prepare_native_hydrometeor_context,
)
from firecloud.shared_geometry.ray import sample_sun_ray_segment, sampled_segment_path_km


class C:
    canvas_id = "canvas::dir+0.0_d5.0_L1"
    cloud_layer_id = "dir+0.0_d5.0_L1"
    distance_km = 5.0
    cloud_base_altitude_km = 2.0


def _route_native():
    rows=[]
    levels=[(1000,100,290),(950,500,288),(900,1000,285),(850,1500,282),(800,2000,280)]
    for d in (0.0,5.0,10.0,15.0):
        r={"point_id":f"+0.0_{int(d):04d}","distance_km":d,"direction_offset_deg":0.0,"precipitation":1.0}
        for p,z,t in levels:
            r[f"geopotential_height_{p}hPa"]=z
            r[f"temperature_{p}hPa"]=t
            r[f"rain_water_kgkg_{p}hPa"]=2e-4 if p in (900,850) else 0.0
            r[f"snow_water_kgkg_{p}hPa"]=1e-5 if p==800 else 0.0
            r[f"graupel_kgkg_{p}hPa"]=0.0
        rows.append(r)
    return pd.DataFrame(rows)


def _legacy_integrate(canvas, cells, solar_altitude_deg, earth_radius_km):
    if not cells:
        return None,0,0,0.0
    tau=0.0; hit=0; unresolved=0; path_km=0.0
    td=float(canvas.distance_km); tz=float(canvas.cloud_base_altitude_km)
    for c in cells:
        if float(c["support_end_km"]) < td-1e-9:
            continue
        a=max(td,float(c["support_start_km"])); b=float(c["support_end_km"])
        if b<=a+1e-9:
            continue
        xs,zz=sample_sun_ray_segment(td,tz,a,b,solar_altitude_deg,sample_count=17,radius_km=earth_radius_km)
        finite=zz[np.isfinite(zz)]
        if finite.size == 0:
            continue
        lo=float(c["z_base_km"]); hi=float(c["z_top_km"])
        if float(np.max(finite))<lo or float(np.min(finite))>hi:
            continue
        hit+=1
        if not bool(c["all_hydrometeor_fields_resolved"]):
            unresolved+=1
        inside=np.isfinite(zz)&(zz>=lo)&(zz<=hi)
        seg_km=sampled_segment_path_km(xs,zz,inside)
        if seg_km>0:
            path_km += seg_km
            tau += max(0.0,float(c["extinction_m1"]))*seg_km*1000.0
    if hit==0:
        relevant=[c for c in cells if float(c["support_end_km"])>=td-1e-9]
        if relevant and all(bool(c["all_hydrometeor_fields_resolved"]) for c in relevant):
            return 0.0,0,0,0.0
        return None,0,len(relevant),0.0
    if unresolved:
        return None,hit,unresolved,path_km
    return float(tau),hit,0,path_km


def test_grouped_integrator_is_exact_legacy_equivalent():
    cells_by_dir,_ = _prepare_native_hydrometeor_cells(_route_native())
    cells=cells_by_dir[0.0]
    groups=_group_cells_by_horizontal_support(cells)
    legacy=_legacy_integrate(C(),cells,-2.0,6371.0)
    grouped=_integrate_sun_path(C(),cells,-2.0,6371.0,support_groups=groups)
    assert grouped == legacy


def test_grouped_integrator_samples_once_per_horizontal_support(monkeypatch):
    cells_by_dir,_ = _prepare_native_hydrometeor_cells(_route_native())
    cells=cells_by_dir[0.0]
    groups=_group_cells_by_horizontal_support(cells)
    td=float(C.distance_km)
    relevant_groups=[g for g in groups if g[1] >= td-1e-9 and g[1] > max(td,g[0])+1e-9]
    calls=0
    original=precipitation.sample_sun_ray_segment
    def counted(*args,**kwargs):
        nonlocal calls
        calls += 1
        return original(*args,**kwargs)
    monkeypatch.setattr(precipitation,"sample_sun_ray_segment",counted)
    _integrate_sun_path(C(),cells,-2.0,6371.0,support_groups=groups)
    assert calls == len(relevant_groups)
    assert calls < sum(1 for c in cells if float(c["support_end_km"]) >= td-1e-9)


def test_prepared_context_science_dataframe_remains_exact():
    snap=_route_native()
    direct=build_precipitation_path_evidence([C()],snap,solar_altitude_deg=-2.0)
    prepared=prepare_native_hydrometeor_context(snap)
    reused=build_precipitation_path_evidence([C()],snap,solar_altitude_deg=-2.0,prepared_native_hydrometeor_context=prepared)
    pd.testing.assert_frame_equal(reused,direct,check_dtype=True,check_exact=True)


def test_version_is_r57413492():
    import firecloud
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.9.2"
