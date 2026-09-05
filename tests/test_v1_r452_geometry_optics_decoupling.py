import math
from firecloud.cloud_scene import ProviderCloudGeometryConfig, classify_native_level, segment_native_levels
from firecloud.contracts import CloudFractionState, EvidenceState

CFG=ProviderCloudGeometryConfig()

def level(z, cf, ql=0.0, qi=0.0, p=800.0, t=280.0):
    return {
        'altitude_agl_km': z, 'cloud_fraction': cf,
        'cloud_liquid_water_kgkg': ql, 'cloud_ice_water_kgkg': qi,
        'pressure_hpa': p, 'temperature_k': t,
    }

def test_cloud_fraction_partial_survives_zero_condensate():
    x=level(2.0,0.276,0.0,0.0)
    assert classify_native_level(x,CFG)==CloudFractionState.PARTIAL_OCCUPANCY
    layers=segment_native_levels([level(1.0,0.0),x,level(3.0,0.0)], direction_offset_deg=0, distance_km=20)
    assert len(layers)==1
    assert layers[0].cloud_fraction_state==CloudFractionState.PARTIAL_OCCUPANCY
    assert layers[0].optical_evidence==EvidenceState.GEOMETRY_ONLY
    assert layers[0].cot is None
    assert layers[0].evidence_consistency=='CF_CLOUD_CONDENSATE_ZERO'

def test_positive_condensate_can_establish_occupancy_when_cf_low():
    x=level(2.0,0.0,2e-6,0.0)
    assert classify_native_level(x,CFG)==CloudFractionState.CLOUD_OCCUPIED
    layers=segment_native_levels([level(1.0,0.0),x,level(3.0,0.0)], direction_offset_deg=0, distance_km=20)
    assert len(layers)==1
    assert layers[0].cot is None
    assert layers[0].evidence_consistency=='CONDENSATE_CLOUD_CF_LOW'
    assert layers[0].optical_evidence==EvidenceState.PARTIAL_OPTICS

def test_consistent_cloud_keeps_native_optics():
    x=level(2.0,0.8,2e-6,1e-6)
    layers=segment_native_levels([level(1.0,0.0),x,level(3.0,0.0)], direction_offset_deg=0, distance_km=20)
    assert len(layers)==1
    assert layers[0].cot is not None and math.isfinite(layers[0].cot)
    assert layers[0].evidence_consistency=='CONSISTENT_CLOUD'
    assert layers[0].optical_evidence==EvidenceState.FULL

def test_partial_cf_zero_condensate_still_creates_canvas_candidate():
    from firecloud.cloud_scene import build_cloud_scene_from_native_route
    from firecloud.v1_runtime import build_canvas_candidates
    import pandas as pd
    row={'direction_offset_deg':0.0,'distance_km':20.0,'native_profile_source':'TEST'}
    for p,z,cf in [(900,1.0,0.0),(850,1.5,0.20),(800,2.0,0.0)]:
        row[f'geopotential_height_{p}hPa']=z*1000.0
        row[f'cloud_fraction_{p}hPa']=cf
        row[f'cloud_liquid_water_kgkg_{p}hPa']=0.0
        row[f'cloud_ice_water_kgkg_{p}hPa']=0.0
        row[f'temperature_{p}hPa']=280.0
        row[f'relative_humidity_{p}hPa']=80.0
    row['model_surface_elevation_m']=0.0
    scene=build_cloud_scene_from_native_route(pd.DataFrame([row]), [900,850,800])
    assert len(scene.layers)==1
    canvases=build_canvas_candidates(scene, observer_lat=24.0, observer_lon=120.0,
                                     solar_azimuth_deg=270.0, earth_radius_km=6371.0)
    assert len(canvases)==1
    assert canvases[0].distance_km==20.0
    assert scene.layers[0].cot is None
