from datetime import datetime, timezone
import pandas as pd
from firecloud.providers import cams_native as c

PTS=[{"point_id":"P0","distance_km":0.0,"direction_offset_deg":0.0,"lat":24.0,"lon":121.0}]
T=datetime(2026,9,3,6,tzinfo=timezone.utc)

def test_three_request_contracts_are_vertically_separated():
    o,_=c.build_ads_ozone_request(PTS,T,pressure_levels_hpa=(1000,500))
    a,_=c.build_ads_native_aerosol_request(PTS,T,pressure_levels_hpa=(1000,500))
    s,_=c.build_ads_spectral_aod_request(PTS,T)
    assert o["variable"] == ["ozone","geopotential"]
    assert "pressure_level" in o
    assert a["variable"] == ["aerosol_extinction_coefficient_532nm","geopotential"]
    assert "pressure_level" in a
    assert "pressure_level" not in s
    assert "total_aerosol_optical_depth_550nm" in s["variable"]
    assert "total_aerosol_optical_depth_670nm" in s["variable"]
    assert all("_at_" not in v for v in s["variable"])

def test_bundle_keeps_ozone_when_aerosol_and_spectral_requests_fail(monkeypatch, tmp_path):
    fake=tmp_path/"o3.grib"; fake.write_bytes(b"x"*2000)
    monkeypatch.setattr(c,"download_native_subset",lambda *a,**k: (_ for _ in ()).throw(RuntimeError("aerosol fail")))
    monkeypatch.setattr(c,"download_ozone_subset",lambda *a,**k:(fake,{"request_audit":{"request_role":"O3_PRESSURE_LEVEL","status":"OK"}}))
    monkeypatch.setattr(c,"_decode_ozone_only",lambda *a,**k:pd.DataFrame({"point_id":["P0"],"cams_ozone_kgkg_500hPa":[1e-6]}))
    monkeypatch.setattr(c,"inspect_grib_message_inventory",lambda *a,**k:pd.DataFrame())
    monkeypatch.setattr(c,"_make_cdsapi_client",lambda: (_ for _ in ()).throw(RuntimeError("spectral fail")))
    out,meta=c.fetch_route_native_aerosol_bundle(PTS,T,cache_dir=tmp_path)
    assert meta["native_aerosol_status"] == "FAILED"
    assert meta["native_ozone_status"] == "OK"
    assert meta["cams_spectral_aod_status"] == "FAILED"
    assert out["cams_ozone_kgkg_500hPa"].notna().any()
    roles={r.get("request_role") for r in meta["cams_request_audit"]}
    assert {"NATIVE_AEROSOL_532NM_PRESSURE_LEVEL","O3_PRESSURE_LEVEL","SPECTRAL_COLUMN_AOD"}.issubset(roles)
