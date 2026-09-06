import numpy as np
import pandas as pd

from firecloud.config import ModelConfig
from firecloud.model import prepare_shared_ray_geometry_plan
from firecloud.shared_geometry.intersections import (
    VoxelIntersectionPlan,
    build_voxel_intersection_plan,
    plan_direction_if_compatible,
)
from firecloud.shared_geometry.ray import ray_altitudes_vectorized_km


def _lattice():
    rows=[]
    for off in (-5.0,0.0,5.0):
        for d in (0.0,10.0,20.0,40.0):
            for z in (0.5,1.0,2.0,4.0,8.0):
                rows.append({"direction_offset_deg":off,"distance_km":d,"voxel_center_km":z})
    return pd.DataFrame(rows)


def test_shared_voxel_intersection_plan_is_geometry_only_and_counted():
    p=build_voxel_intersection_plan(_lattice(),-2.0,radius_km=6371.0)
    assert isinstance(p,VoxelIntersectionPlan)
    assert p.target_plan_count == 3*4*5
    assert p.segment_count > 0
    assert 0 <= p.valid_segment_count <= p.segment_count
    legacy=p.as_legacy_dict()
    text=repr(legacy).lower()
    for forbidden in ("cloud_occupancy","condensate","extinction_m1","transmission","aod","cot"):
        assert forbidden not in text


def test_plan_nearest_height_matches_legacy_searchsorted_rule():
    df=_lattice(); angle=-2.0; radius=6371.0
    p=build_voxel_intersection_plan(df,angle,radius_km=radius)
    d=p.directions[0.0]
    heights=d["heights"]
    rec=d["targets"][(10.0,4.0)]
    ds=rec["ds"]
    prev=np.concatenate(([10.0],ds[:-1])); dx=ds-prev; mids=ds-dx/2.0
    ray=ray_altitudes_vectorized_km(10.0,4.0,mids,angle,radius)
    hi=np.searchsorted(heights,ray,side="left"); hi=np.clip(hi,0,len(heights)-1)
    lo=np.clip(hi-1,0,len(heights)-1)
    choose_hi=np.abs(heights[hi]-ray)<np.abs(ray-heights[lo])
    expected=np.where(choose_hi,hi,lo)
    assert np.array_equal(rec["nearest_height_index"],expected)


def test_compatibility_wrapper_and_exact_lattice_guard():
    df=_lattice(); cfg=ModelConfig()
    plan=prepare_shared_ray_geometry_plan(df,-1.5,cfg)
    assert plan["plan_type"] == "VOXEL_INTERSECTION_PLAN_V1"
    d=plan["directions"][0.0]
    assert plan_direction_if_compatible(plan,0.0,d["distances"],d["heights"]) is d
    bad=d["heights"].copy(); bad[-1]+=0.001
    assert plan_direction_if_compatible(plan,0.0,d["distances"],bad) is None
