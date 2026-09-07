import numpy as np
import pandas as pd

from firecloud.shared_geometry.intersections import (
    build_voxel_intersection_topology,
    materialize_voxel_intersection_plan,
    voxel_lattice_key,
)


def _lattice():
    rows=[]
    for off in (-5.0,0.0,5.0):
        for d in (0.0,10.0,20.0,40.0):
            for z in (0.25,0.75,1.25,1.75):
                rows.append({"direction_offset_deg":off,"distance_km":d,"voxel_center_km":z})
    return pd.DataFrame(rows)


def test_lattice_key_ignores_optical_values_but_tracks_geometry():
    a=_lattice(); b=a.copy(); b["cloud_occupancy"]=np.arange(len(b),dtype=float)
    assert voxel_lattice_key(a)==voxel_lattice_key(b)
    c=b.copy(); c.loc[c.index[0],"voxel_center_km"]=0.30
    assert voxel_lattice_key(a)!=voxel_lattice_key(c)


def test_cross_angle_topology_reuse_preserves_angle_independent_segments():
    df=_lattice(); topo=build_voxel_intersection_topology(df)
    p1=materialize_voxel_intersection_plan(topo,-1.0,topology_cache_status="MISS_BUILT")
    p2=materialize_voxel_intersection_plan(topo,-3.0,topology_cache_status="HIT_CROSS_ANGLE")
    assert p1.target_plan_count==p2.target_plan_count==len(df)
    assert p1.segment_count==p2.segment_count
    assert p1.topology_cache_status=="MISS_BUILT"
    assert p2.topology_cache_status=="HIT_CROSS_ANGLE"
    for off in p1.directions:
        d1=p1.directions[off]; d2=p2.directions[off]
        assert np.array_equal(d1["distances"],d2["distances"])
        assert np.array_equal(d1["heights"],d2["heights"])
        for key in d1["targets"]:
            t1=d1["targets"][key]; t2=d2["targets"][key]
            assert np.array_equal(t1["ds"],t2["ds"])
            assert np.array_equal(t1["dx"],t2["dx"])
            assert np.array_equal(t1["upstream_row_index"],t2["upstream_row_index"])
            # Angle-dependent ray heights must remain independently materialized.
            if t1["ray_height_km"].size:
                assert not np.array_equal(t1["ray_height_km"],t2["ray_height_km"])


def test_ray_matrix_matches_vectorized_scalar_height_calls():
    from firecloud.shared_geometry.ray import ray_altitude_matrix_km, ray_altitudes_vectorized_km
    heights=np.array([0.25,1.25,5.25,12.25],dtype=float)
    samples=np.array([45.0,60.0,80.0,120.0],dtype=float)
    m=ray_altitude_matrix_km(40.0,heights,samples,-2.0)
    assert m.shape==(len(heights),len(samples))
    for i,z in enumerate(heights):
        ref=ray_altitudes_vectorized_km(40.0,float(z),samples,-2.0)
        assert np.allclose(m[i],ref,equal_nan=True,rtol=0.0,atol=1e-12)
