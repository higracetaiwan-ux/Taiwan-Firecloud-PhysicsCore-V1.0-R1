import numpy as np
import firecloud.geometry as legacy
from firecloud.shared_geometry import (
    ray_altitude_km_at_surface_distance,
    ray_altitudes_vectorized_km,
    observer_los_height_agl_km,
    direct_solar_fraction_g0,
    GeometryIdentity,
    SharedGeometryContext,
)
from firecloud import viewing, precipitation


def test_scalar_vectorized_solar_ray_are_identical():
    ds=np.array([5.,10.,20.,30.,40.])
    vec=ray_altitudes_vectorized_km(40.,8.,ds,-2.0,6371.0)
    scalar=np.array([ray_altitude_km_at_surface_distance(40.,8.,float(d),-2.0,6371.0) for d in ds],dtype=float)
    assert np.allclose(vec,scalar,equal_nan=True,rtol=0,atol=1e-12)


def test_viewing_and_precipitation_share_single_los_primitive():
    assert viewing._los_height_agl_km is observer_los_height_agl_km
    # precipitation no longer owns a duplicate private LOS implementation
    assert not hasattr(precipitation, '_observer_los_height_km')
    assert observer_los_height_agl_km(40.,12.,5.,6371.) > 0


def test_legacy_geometry_facade_matches_shared_core():
    assert legacy.ray_altitude_km_at_surface_distance is ray_altitude_km_at_surface_distance
    assert legacy.direct_solar_fraction_g0 is direct_solar_fraction_g0
    assert legacy.dynamic_rez_entry_distance_km(-2.0,8.0)==legacy.dynamic_rez_entry_distance_km(-2.0,8.0)


def test_shared_geometry_context_is_geometry_only_container():
    ctx=SharedGeometryContext(GeometryIdentity(observer_lat=24.0,observer_lon=120.0))
    bucket=ctx.angle_bucket(-2.0); bucket['ray_plan']={'ok':True}
    assert ctx.angle_bucket(-2.0)['ray_plan']['ok'] is True
    forbidden={'cot','tau','transmission','brightness','redness','cloud_fraction'}
    assert not (forbidden & set(ctx.event_fixed))
