from pathlib import Path
import os
import pandas as pd

from firecloud.providers import cams_native as c


def test_credentials_are_stripped(monkeypatch):
    monkeypatch.setenv("ADS_API_KEY", "  abc123  ")
    monkeypatch.setenv("ADS_API_URL", "  https://ads.atmosphere.copernicus.eu/api  ")
    url, key, src = c._credential_env()
    assert key == "abc123"
    assert url == "https://ads.atmosphere.copernicus.eu/api"
    assert src == "ADS_ENV"


def test_ozone_match_uses_shortname_even_when_name_present():
    vals={"shortName":"o3","name":"Ozone","paramId":203,"units":"kg kg-1"}
    def get(_gid, key): return vals[key]
    assert c._is_ozone(object(), get) is True


def test_aerosol_and_ozone_status_are_independent(monkeypatch, tmp_path):
    fake=tmp_path/"x.grib"; fake.write_bytes(b"x"*2000)
    monkeypatch.setattr(c, "download_native_subset", lambda *a, **k: (fake, {"cams_run_utc":"2026-09-03T00:00:00+00:00"}))
    df=pd.DataFrame({"point_id":["P0"],"cams_ozone_kgkg_500hPa":[1e-6]})
    monkeypatch.setattr(c, "decode_grib_to_route", lambda *a, **k: df)
    monkeypatch.setattr(c, "inspect_grib_message_inventory", lambda *a, **k: pd.DataFrame([{"shortName":"o3","name":"Ozone"}]))
    out, meta=c.fetch_route_native_aerosol([{"point_id":"P0","distance_km":0,"direction_offset_deg":0,"lat":24,"lon":121}], __import__('datetime').datetime(2026,9,3))
    assert meta["native_aerosol_status"] == "MISSING"
    assert meta["native_ozone_status"] == "OK"
    assert meta["native_ozone_error"] == ""
    assert "cams_ozone_kgkg_500hPa" in out.columns
