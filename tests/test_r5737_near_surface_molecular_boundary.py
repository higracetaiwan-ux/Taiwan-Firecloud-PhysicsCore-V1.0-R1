from datetime import datetime, timezone
from types import SimpleNamespace

import numpy as np
import pandas as pd

from firecloud import gas_rt, twilight_glow
from firecloud.providers import cams_native, openmeteo


def _snapshot_row(point_id='p0', *, surface_pressure=1015.0, temperature_2m=300.0, rh_2m=70.0):
    return {
        'point_id': point_id,
        'distance_km': 0.0,
        'direction_offset_deg': 0.0,
        'surface_pressure': surface_pressure,
        'temperature_2m': temperature_2m,
        'relative_humidity_2m': rh_2m,
        'model_surface_elevation_m': 0.0,
        'geopotential_height_1000hPa': 96.0,
        'temperature_1000hPa': 298.0,
        'relative_humidity_1000hPa': 75.0,
        'geopotential_height_950hPa': 550.0,
        'temperature_950hPa': 295.0,
        'relative_humidity_950hPa': 60.0,
    }


def _ozone_row(point_id='p0', *, ml137=8e-8):
    return {
        'point_id': point_id,
        'cams_ozone_ml137_kgkg': ml137,
        'cams_ozone_kgkg_1000hPa': 9e-8,
        'cams_ozone_kgkg_950hPa': 1e-7,
    }


def _target():
    return pd.Series({
        'time':'t0', 'solar_altitude_deg':-6.0, 'direction_offset_deg':0.0,
        'target_distance_km':100.0, 'target_base_km':3.5, 'target_top_km':4.0,
    })


def test_r5737_openmeteo_surface_contract_includes_near_surface_thermodynamics():
    assert 'surface_pressure' in openmeteo.SURFACE_HOURLY_VARS
    assert 'temperature_2m' in openmeteo.SURFACE_HOURLY_VARS
    assert 'relative_humidity_2m' in openmeteo.SURFACE_HOURLY_VARS


def test_r5737_cams_ml137_request_is_separate_native_model_level_contract():
    pts=[{'point_id':'p0','distance_km':0.0,'direction_offset_deg':0.0,'lat':24.0,'lon':121.0}]
    req,meta=cams_native.build_ads_near_surface_ozone_request(pts,datetime(2026,9,10,10,tzinfo=timezone.utc))
    assert req['variable']==['ozone']
    assert req['model_level']==['137']
    assert 'pressure_level' not in req
    assert meta['request_role']=='O3_NEAR_SURFACE_MODEL_LEVEL_137'


def test_r5737_gas_profile_adds_ml137_anchor_below_pressure_level_profile():
    snap=pd.DataFrame([_snapshot_row()])
    o3=pd.DataFrame([_ozone_row()])
    out=gas_rt.build_gas_profile(snap,[1000,950],ozone_snapshot=o3)
    anchor=out[out['near_surface_boundary_state'].astype(str)=='READY']
    assert len(anchor)==1
    a=anchor.iloc[0]
    assert 0.005 < float(a['altitude_agl_km']) < 0.02
    assert abs(float(a['pressure_hpa'])/1015.0-gas_rt.ECMWF_L137_FULL_PRESSURE_RATIO) < 1e-12
    assert a['o3_quality']=='CAMS_MODEL_LEVEL_137_OZONE_NATIVE_NEAR_SURFACE_ANCHOR'
    assert out['altitude_agl_km'].min() < 0.02
    assert out['altitude_agl_km'].max() >= 0.55


def test_r5737_missing_surface_or_ml137_evidence_does_not_create_anchor():
    snap=pd.DataFrame([_snapshot_row(rh_2m=np.nan)])
    o3=pd.DataFrame([_ozone_row()])
    out=gas_rt.build_gas_profile(snap,[1000,950],ozone_snapshot=o3)
    assert 'near_surface_boundary_state' not in out.columns or not (out['near_surface_boundary_state'].astype(str)=='READY').any()
    snap2=pd.DataFrame([_snapshot_row()])
    o32=pd.DataFrame([_ozone_row(ml137=np.nan)])
    out2=gas_rt.build_gas_profile(snap2,[1000,950],ozone_snapshot=o32)
    assert 'near_surface_boundary_state' not in out2.columns or not (out2['near_surface_boundary_state'].astype(str)=='READY').any()


def test_r5737_ml137_anchor_closes_true_21m_gap_without_widening_10m_tolerance():
    assert gas_rt.DEFAULT_PROFILE_BOUNDARY_TOLERANCE_KM == 0.01
    # Existing native pressure-level floor is 96 m; ML137 adds a real ~10 m anchor.
    profile=pd.DataFrame({
        'altitude_agl_km':[0.010,0.096,0.55,1.0,5.0,10.0],
        'temperature_k':[300.0,298.0,295.0,290.0,255.0,225.0],
        'pressure_hpa':[1013.8,1000.0,950.0,900.0,500.0,250.0],
    })
    profiles={float(d):profile.copy() for d in np.arange(0.0,105.0,5.0)}
    tau,status,required,resolved=twilight_glow._rayleigh_observer_path(_target(),profiles,6371.0)
    assert status=='GLOW_OBSERVER_RAYLEIGH_PATH_RESOLVED'
    assert required==resolved>0
    assert all(v>0 for v in tau.values())


def test_r5737_gas_species_resolves_with_ml137_bracket(monkeypatch):
    z=np.array([0.010,0.096,0.55,1.0,5.0,10.0],dtype=float)
    rec={
        'z':z,
        'temperature_k':np.array([300.,298.,295.,290.,255.,225.]),
        'pressure_hpa':np.array([1013.8,1000.,950.,900.,500.,250.]),
        'o2_mole_fraction':np.array([0.20946]*len(z)),
        'h2o_mole_fraction':np.array([0.015,0.014,0.010,0.006,0.001,0.0002]),
        'o3_mole_fraction':np.array([5e-8,5.5e-8,6e-8,7e-8,1e-7,4e-7]),
    }
    distances=np.arange(0.0,105.0,5.0)
    ctx=SimpleNamespace(valid=True,prepared_profile={0.0:{'distances':distances,'profiles':{float(d):rec for d in distances}}},lut={})
    monkeypatch.setattr(twilight_glow,'_sigma_fast',lambda *_a,**_k:1e-27)
    tau,status,required,resolved,path_km=twilight_glow._observer_gas_species_path(_target(),ctx,6371.0)
    assert status=='GLOW_OBSERVER_GAS_PATH_RESOLVED'
    assert required==resolved>0
    assert path_km>100.0
    assert all(tau[int(w)]['total']>0 for w in twilight_glow.SIX_BAND_WAVELENGTHS_NM)


def test_r5737_boundary_diagnostics_preserve_pressure_level_gap_and_record_real_bridge():
    profile=pd.DataFrame({
        'altitude_agl_km':[0.010,0.096,0.55,1.0,5.0,10.0],
        'temperature_k':[300.0,298.0,295.0,290.0,255.0,225.0],
        'pressure_hpa':[1013.8,1000.0,950.0,900.0,500.0,250.0],
        'near_surface_boundary_state':['READY','','','','',''],
    })
    profiles={float(d):profile.copy() for d in np.arange(0.0,105.0,5.0)}
    diag=twilight_glow._molecular_boundary_diagnostics(_target(),profiles,6371.0)
    assert diag['near_surface_anchor_segment_count'] > 0
    assert diag['near_surface_bridge_segment_count'] > 0
    assert float(diag['pressure_level_only_raw_max_gap_km']) > 0.01
    # The real ML137 anchor makes the actual lowest-boundary gap zero; no wider snap is needed.
    assert float(diag['raw_max_gap_km']) == 0.0
    assert int(diag['snap_segment_count']) == 0


def _integrity_status(audit, check_id):
    rows=audit[audit['check_id'].eq(check_id)]
    assert len(rows)==1, (check_id, audit[['check_id','status']].to_dict('records'))
    return rows.iloc[0]['status']


def test_r5737_integrity_requires_native_anchor_provenance_and_frozen_10m_tolerance():
    from firecloud.case_integrity import build_analysis_integrity_audit, PASS
    gas=pd.DataFrame([{
        'temperature_k':300.0,'pressure_hpa':1013.8,'h2o_mole_fraction':0.015,'o2_mole_fraction':0.20946,
        'o3_mass_mixing_ratio_kgkg':8e-8,'altitude_agl_km':0.010,
        'near_surface_boundary_state':'READY',
        'near_surface_boundary_contract':gas_rt.NEAR_SURFACE_MOLECULAR_BOUNDARY_CONTRACT,
        'o3_quality':'CAMS_MODEL_LEVEL_137_OZONE_NATIVE_NEAR_SURFACE_ANCHOR',
    }])
    observer=pd.DataFrame([{
        'distance_km':100.0,
        'glow_observer_molecular_lowest_endpoint_tolerance_km':0.01,
        'glow_observer_near_surface_boundary_bridge_segment_count':1,
        'glow_observer_pressure_level_only_raw_max_gap_km':0.021,
        'glow_observer_near_surface_boundary_contract':gas_rt.NEAR_SURFACE_MOLECULAR_BOUNDARY_CONTRACT,
        'glow_observer_rayleigh_status':'GLOW_OBSERVER_RAYLEIGH_PATH_RESOLVED',
        'glow_observer_gas_species_status':'GLOW_OBSERVER_GAS_PATH_RESOLVED',
    }])
    result={
        'near_surface_molecular_boundary_closure_required':True,
        'gas_profile_route_snapshots':gas,
        'cams_request_audit':pd.DataFrame({'role':['O3_NEAR_SURFACE_MODEL_LEVEL_137'],'status':['OK']}),
        'v1_twilight_glow_scatter_to_observer_extinction_550_750nm':observer,
    }
    audit=build_analysis_integrity_audit(result)
    assert _integrity_status(audit,'NEAR_SURFACE_MOLECULAR_BOUNDARY_ANCHOR_PROVENANCE') == PASS
    assert _integrity_status(audit,'NEAR_SURFACE_MOLECULAR_BOUNDARY_FROZEN_10M_TOLERANCE') == PASS
    assert _integrity_status(audit,'NEAR_SURFACE_MOLECULAR_BOUNDARY_BRIDGE_PROVENANCE') == PASS


def test_r5737_integrity_rejects_widened_boundary_tolerance():
    from firecloud.case_integrity import build_analysis_integrity_audit, FAIL
    observer=pd.DataFrame([{
        'distance_km':100.0,
        'glow_observer_molecular_lowest_endpoint_tolerance_km':0.02,
        'glow_observer_near_surface_boundary_bridge_segment_count':0,
    }])
    audit=build_analysis_integrity_audit({
        'near_surface_molecular_boundary_closure_required':True,
        'v1_twilight_glow_scatter_to_observer_extinction_550_750nm':observer,
    })
    assert _integrity_status(audit,'NEAR_SURFACE_MOLECULAR_BOUNDARY_FROZEN_10M_TOLERANCE') == FAIL
