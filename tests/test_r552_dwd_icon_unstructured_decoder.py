from pathlib import Path
from types import SimpleNamespace
import sys

import numpy as np
from scipy.io import netcdf_file

from firecloud.providers import dwd_icon_native as icon


def _weights(path: Path):
    with netcdf_file(str(path), "w") as nc:
        nc.createDimension("num_links", 4)
        src=nc.createVariable("src_address", "i", ("num_links",))
        dst=nc.createVariable("dst_address", "i", ("num_links",))
        src[:] = np.array([3,1,4,2], dtype=np.int32)  # 1-based source
        dst[:] = np.array([1,2,3,4], dtype=np.int32)  # 1-based target


def test_cdo_gennn_source_address_is_converted_to_zero_based(tmp_path):
    p=tmp_path/"weights.nc"; _weights(p)
    m=icon._read_nn_source_map(p)
    assert m[:4].tolist() == [2,0,3,1]


def test_target_grid_world_025_contract():
    dst,lat,lon=icon._target_grid_cell(24.0,121.0)
    assert lat == 24.0 and lon == 121.0
    assert dst == (456*1440 + 484 + 1)


def test_decode_nearest_uses_source_address_not_grib_lat_lon(monkeypatch, tmp_path):
    calls=[]
    fake_gid=object()
    fake=SimpleNamespace(
        codes_grib_new_from_file=lambda f: fake_gid,
        codes_get_array=lambda gid,key: (calls.append(key) or np.array([10.0,20.0,30.0,40.0])) if key=="values" else (_ for _ in ()).throw(AssertionError(key)),
        codes_get=lambda gid,key: {"units":"kg kg-1","shortName":"qc","level":91,"gridType":"unstructured_grid","packingType":"grid_ccsds","numberOfGridUsed":26}[key],
        codes_release=lambda gid: None,
    )
    monkeypatch.setitem(sys.modules,"eccodes",fake)
    monkeypatch.setattr(icon,"decoder_available",lambda: True)
    f=tmp_path/"dummy.grib2"; f.write_bytes(b"GRIB")
    points=[{"point_id":"p","distance_km":40.0,"direction_offset_deg":0.0,"lat":24.0,"lon":121.0}]
    source_map={"p":{"source_index":2,"dst_address":123,"target_grid_lat":24.0,"target_grid_lon":121.0}}
    df,meta=icon._decode_nearest(f,points,source_map=source_map)
    assert calls == ["values"]
    assert float(df.iloc[0].value) == 30.0
    assert int(df.iloc[0].icon_source_index) == 2
    assert meta["grid_type"] == "unstructured_grid"
    assert meta["packing_type"] == "grid_ccsds"


def test_grid_mapping_failure_stops_before_field_download(monkeypatch):
    monkeypatch.setattr(icon,"decoder_available",lambda: True)
    monkeypatch.setattr(icon,"remap_reader_available",lambda: True)
    monkeypatch.setattr(icon,"network_enabled",lambda: True)
    monkeypatch.setattr(icon,"_route_source_index_map",lambda *a,**k: (_ for _ in ()).throw(RuntimeError("no map")))
    called={"n":0}
    def bad_fetch(*a,**k):
        called["n"]+=1
        raise AssertionError("field download must not start")
    monkeypatch.setattr(icon,"_fetch_field",bad_fetch)
    pts=[{"point_id":"p","distance_km":40.0,"direction_offset_deg":0.0,"lat":24.0,"lon":121.0}]
    prof,meta,audit=icon.fetch_icon_route_profiles(pts, __import__('datetime').datetime(2026,9,6,10,tzinfo=__import__('datetime').timezone.utc))
    assert prof.empty
    assert meta["status"] == "GRID_MAPPING_FAILED"
    assert called["n"] == 0
    assert "GRID_MAPPING_FAILED" in set(audit["status"])
