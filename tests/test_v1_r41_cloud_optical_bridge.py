import math
import pandas as pd

from firecloud.cloud_scene import segment_native_levels
from firecloud.contracts import (
    CanvasCandidate, CanvasDomain, CloudFractionState, CloudLayer, CloudScene,
    EvidenceState, GeometryConfidence, SIX_BAND_WAVELENGTHS_NM,
)
from firecloud.formation import build_r4_formation_tables


def _native_levels(with_condensate=True):
    rows=[]
    for p,z,cf in [(700,3.0,0.8),(650,3.8,0.9),(600,4.7,0.85)]:
        rows.append({
            'pressure_hpa':p, 'altitude_agl_km':z, 'cloud_fraction':cf,
            'cloud_liquid_water_kgkg': 8e-5 if with_condensate else float('nan'),
            'cloud_ice_water_kgkg': 3e-5 if with_condensate else float('nan'),
            'temperature_k':275.0, 'relative_humidity_pct':90.0,
        })
    return rows


def test_r41_native_condensate_produces_layer_cot_without_cloud_fraction_proxy():
    layers=segment_native_levels(_native_levels(True), direction_offset_deg=0.0, distance_km=20.0)
    assert len(layers)==1
    layer=layers[0]
    assert layer.optical_evidence == EvidenceState.FULL
    assert layer.cot is not None and math.isfinite(layer.cot) and layer.cot > 0
    assert layer.effective_radius_um is not None
    assert any(p.source_type.value == 'DERIVED_PHYSICAL' for p in layer.provenance)


def test_r41_geometry_only_never_gets_cot():
    layers=segment_native_levels(_native_levels(False), direction_offset_deg=0.0, distance_km=20.0)
    assert len(layers)==1
    layer=layers[0]
    assert layer.optical_evidence == EvidenceState.GEOMETRY_ONLY
    assert layer.cot is None
    assert layer.effective_radius_um is None


def test_r41_formation_can_use_cloudlayer_native_cot_without_legacy_voxel_cot():
    layer=CloudLayer(
        layer_id='target', direction_offset_deg=0.0, distance_km=20.0,
        z_base_km=5.0, z_top_km=6.0,
        cloud_fraction_state=CloudFractionState.CLOUD_OCCUPIED,
        cloud_fraction=0.8, phase='ICE', effective_radius_um=30.0, cot=2.0,
        geometry_confidence=GeometryConfidence.HIGH, optical_evidence=EvidenceState.FULL,
    )
    scene=CloudScene(valid_time=None, layers=(layer,), geometry_completeness=1.0, optics_completeness=1.0)
    canvas=CanvasCandidate(
        canvas_id='c', cloud_layer_id='target', latitude=24.0, longitude=120.0,
        cloud_base_altitude_km=5.0, distance_km=20.0, azimuth_deg=270.0,
        operational_domain=CanvasDomain.PRIMARY_CANVAS_0_40,
        geometry_confidence=GeometryConfidence.HIGH,
    )
    illum={'canvas_id':'c','direct_solar_fraction':1.0,'illumination_status':'FULL_RT','spectral_transmission_complete':True}
    for wl in SIX_BAND_WAVELENGTHS_NM:
        illum[f'relative_base_illumination_{wl}nm']=0.5
    out=build_r4_formation_tables(
        scene=scene, canvases=[canvas], cloud_base_illumination=pd.DataFrame([illum]),
        spectral_voxels=pd.DataFrame(), solar_altitude_deg=-2.0,
    )
    row=out['canvas_radiance'].iloc[0]
    assert row['response_status']=='READY_TIER1_UNCALIBRATED'
    assert row['target_vertical_cloud_optical_depth']==2.0
    assert row['target_cloud_cot_source']=='CLOUD_LAYER_NATIVE_CONDENSATE'
