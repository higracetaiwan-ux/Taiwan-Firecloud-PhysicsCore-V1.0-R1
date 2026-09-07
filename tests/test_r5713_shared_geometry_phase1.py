import numpy as np

from firecloud.shared_geometry import (
    geodetic_to_ecef, ecef_to_geodetic, ecef_to_enu, enu_to_ecef,
    ray_sphere_intersections, VerticalIndexPlan, center_layer_bounds_km,
)
from firecloud.shared_geometry.ray import ray_altitude_matrix_km
from firecloud.gas_rt import _ray_altitudes_matrix


def test_wgs84_geodetic_ecef_roundtrip():
    lat,lon,h=25.0330,121.5654,42.0
    x,y,z=geodetic_to_ecef(lat,lon,h)
    a,b,c=ecef_to_geodetic(x,y,z)
    assert abs(a-lat)<1e-8
    assert abs(b-lon)<1e-8
    assert abs(c-h)<1e-4


def test_enu_ecef_roundtrip():
    ref=(25.0,121.0,123.0)
    e,n,u=(1500.0,-2300.0,450.0)
    xyz=enu_to_ecef(e,n,u,*ref)
    got=ecef_to_enu(*xyz,*ref)
    assert np.allclose(got,(e,n,u),atol=1e-6,rtol=0)


def test_ray_sphere_intersection_contract():
    hit=ray_sphere_intersections((7000.0,0.0,0.0),(-1.0,0.0,0.0),6371.0)
    assert hit is not None
    assert np.allclose(hit,(629.0,13371.0),atol=1e-12)


def test_vertical_index_tie_resolves_lower():
    p=VerticalIndexPlan.from_centers([0.0,1.0,2.0,3.0])
    got=p.nearest_indices(np.array([0.5,1.5,2.5]))
    assert got.tolist()==[0,1,2]


def test_center_layer_bounds_are_contiguous():
    lo,hi=center_layer_bounds_km([1.0,2.0,4.0])
    assert np.allclose(hi[:-1],lo[1:])
    assert np.all(hi>lo)


def test_gas_ray_matrix_delegates_to_shared_geometry():
    z=[1.0,5.0,10.0]; ds=[25.0,50.0,75.0]
    a=_ray_altitudes_matrix(100.0,z,ds,-2.0,6371.0)
    b=ray_altitude_matrix_km(100.0,z,ds,-2.0,6371.0)
    assert np.allclose(a,b,equal_nan=True,atol=0,rtol=0)
