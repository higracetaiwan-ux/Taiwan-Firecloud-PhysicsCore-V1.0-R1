import pandas as pd
from firecloud.cloud_scene import segment_native_levels
from firecloud.contracts import CloudFractionState, CloudLayer, CloudScene, EvidenceState, GeometryConfidence, CanvasCandidate, CanvasDomain
from firecloud.optical_path import build_r3_optical_tables
from firecloud.precipitation import build_precipitation_path_evidence

def test_geometry_only_cloud_never_becomes_tau_zero_from_transmission_one():
    layer=CloudLayer('t',0,20,5,6,CloudFractionState.CLOUD_OCCUPIED,geometry_confidence=GeometryConfidence.HIGH,optical_evidence=EvidenceState.GEOMETRY_ONLY)
    scene=CloudScene(None,(layer,),1,0)
    c=CanvasCandidate('c','t',24,120,5,20,270,CanvasDomain.PRIMARY_CANVAS_0_40,GeometryConfidence.HIGH)
    vox=pd.DataFrame([{'direction_offset_deg':0.0,'distance_km':20.0,'voxel_bottom_km':4.5,'voxel_top_km':5.5,**{f'cloud_transmission_{w}nm':1.0 for w in (550,575,600,650,700,750)}}])
    out=build_r3_optical_tables(scene=scene,canvases=[c],direct_solar=pd.DataFrame([{'canvas_id':'c','direct_solar_fraction':1.0}]),solar_rays=pd.DataFrame(),spectral_voxels=vox,solar_altitude_deg=0,earth_radius_km=6371)
    assert out['spectral_optical_paths']['tau_cloud'].isna().all()

def test_single_native_level_has_finite_native_support():
    levels=[{'altitude_agl_km':4.0,'cloud_fraction':0.0},{'altitude_agl_km':5.0,'cloud_fraction':0.8},{'altitude_agl_km':6.0,'cloud_fraction':0.0}]
    layers=segment_native_levels(levels,direction_offset_deg=0,distance_km=20)
    assert len(layers)==1 and layers[0].z_top_km>layers[0].z_base_km
    assert abs(layers[0].z_base_km-4.5)<1e-9 and abs(layers[0].z_top_km-5.5)<1e-9

def test_precip_surface_rate_does_not_fabricate_tau():
    class C: canvas_id='c'
    p=build_precipitation_path_evidence([C()], pd.DataFrame([{'precipitation':2.0}]))
    assert p.iloc[0]['status']=='PRECIPITATION_VOLUME_UNRESOLVED'
    assert p.iloc[0]['optical_evidence']=='MISSING'
