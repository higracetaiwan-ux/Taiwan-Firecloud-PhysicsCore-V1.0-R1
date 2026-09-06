from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

from firecloud.providers import cams_native, gfs_native, dwd_icon_native


def _pts():
    return [{"point_id":"p0","distance_km":0.0,"direction_offset_deg":0.0,"lat":24.25,"lon":120.5,
             "surface_pressure_hpa":1008.0,"surface_elevation_m":12.0}]


def test_cams_decoded_route_cache_skips_worker(monkeypatch, tmp_path):
    pts=_pts(); t=datetime(2026,9,6,9,tzinfo=timezone.utc)
    df=pd.DataFrame({"point_id":["p0"],"cams_ozone_kgkg_100":[1e-6]})
    result={"role":"O3_PRESSURE_LEVEL","status":"OK","df":df,"meta":{"request_audit":{"status":"OK"}},"inventory":[],"error":""}
    cams_native._save_decoded_role_cache("O3_PRESSURE_LEVEL",pts,t,result,tmp_path)
    def boom(*a,**k):
        raise AssertionError("subprocess should not be started on decoded cache hit")
    monkeypatch.setattr(cams_native.subprocess,"Popen",boom)
    out=cams_native._run_cams_role_isolated("O3_PRESSURE_LEVEL",pts,t,tmp_path,deadline_seconds=1)
    assert out["status"]=="CACHE_HIT"
    assert out["worker_mode"]=="WORKER_SKIPPED_DECODED_CACHE_HIT"
    assert out["meta"]["decoded_route_cache_status"]=="HIT"


def test_gfs_decoded_route_cache_roundtrip(tmp_path):
    grib=tmp_path/"x.grib2"; grib.write_bytes(b"not-used")
    pts=_pts(); df=pd.DataFrame({"point_id":["p0"],"temperature_k_1000hPa":[300.0]})
    gfs_native._save_decoded_cache(grib,pts,df)
    got=gfs_native._load_decoded_cache(grib,pts)
    assert isinstance(got,pd.DataFrame)
    assert float(got.iloc[0]["temperature_k_1000hPa"])==300.0


def test_dwd_persistent_optics_cache_includes_surface_anchor(tmp_path, monkeypatch):
    monkeypatch.setenv("FIRECLOUD_DWD_ICON_CACHE_DIR",str(tmp_path))
    run=datetime(2026,9,6,6,tzinfo=timezone.utc); lead=3
    pts=_pts(); optics=pd.DataFrame({"point_id":["p0"],"cot":[1.0]}); meta={"status":"FULL_NATIVE_MICROPHYSICS"}
    dwd_icon_native._save_persistent_optics_cache(run,lead,pts,optics,meta)
    got=dwd_icon_native._load_persistent_optics_cache(run,lead,pts)
    assert got is not None
    p1=dwd_icon_native._persistent_optics_cache_path(run,lead,pts)
    pts2=_pts(); pts2[0]["surface_pressure_hpa"]=1000.0
    p2=dwd_icon_native._persistent_optics_cache_path(run,lead,pts2)
    assert p1 != p2
