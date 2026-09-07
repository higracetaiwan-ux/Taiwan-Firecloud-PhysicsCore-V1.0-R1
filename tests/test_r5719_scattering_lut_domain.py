import hashlib
import json
import pandas as pd

from firecloud.tier2_scattering_runtime import validate_scattering_lut_bytes, install_scattering_lut, load_installed_scattering_lut
from firecloud.tier2_scattering_domain import evaluate_tier2_scattering_domain, summarize_tier2_scattering_domain

WLS=[550,575,600,650,700,750]


def full_grid(phase='LIQUID'):
    rows=[]
    for wl in WLS:
        for cot in [1.0,3.0]:
            for reff in [8.0,12.0]:
                for thick in [0.5,1.5]:
                    for angle in [60.0,120.0]:
                        rows.append({
                            'phase':phase,'wavelength_nm':wl,'cot':cot,'effective_radius_um':reff,
                            'cloud_thickness_km':thick,'scattering_angle_deg':angle,
                            'response_factor':0.2 + wl/10000.0,'calibration_state':'CALIBRATED','lut_version':'TEST19',
                        })
    return pd.DataFrame(rows)


def manifest_bytes(csv_bytes, phases=('LIQUID',)):
    d={
        'contract':'R5.7.19_TIER2_SCATTERING_LUT_RUNTIME_V1',
        'lut_version':'TEST19','calibration_state':'CALIBRATED','calibration_id':'CAL-001',
        'calibration_source':'SYNTHETIC_REGRESSION_ONLY','calibration_date':'2026-09-07',
        'required_wavelengths_nm':WLS,'supported_phases':list(phases),
        'csv_sha256':hashlib.sha256(csv_bytes).hexdigest(),
    }
    return json.dumps(d).encode()


def audit_and_lut(df=None):
    df=full_grid() if df is None else df
    b=df.to_csv(index=False).encode()
    audit=validate_scattering_lut_bytes(b,manifest_bytes(b))
    assert audit['ok'], audit
    q=pd.read_csv(pd.io.common.BytesIO(b))
    return audit,q


def readiness(truth='EXACT_PRIMARY_NATIVE', sem='EXACT_VALUE', lo=2.0, hi=2.0, phase='LIQUID', reff=10.0, thick=1.0):
    return pd.DataFrame([{
        'canvas_id':'c1','tier2_input_contract_state':'INPUTS_READY_AWAITING_LUT_SOLVER',
        'target_optical_truth_state':truth,'target_cot_semantics':sem,'phase':phase,
        'cot_lower_bound':lo,'cot_upper_bound':hi,'effective_radius_um':reff,'cloud_thickness_km':thick,
    }])


def foundation(angle=90.0):
    return pd.DataFrame([{
        'time':'t','solar_altitude_deg':-2.0,'canvas_id':'c1','cloud_layer_id':'l1',
        'operational_domain':'PRIMARY_CANVAS_0_40','distance_km':20.0,
        'tier2_input_contract_state':'INPUTS_READY_AWAITING_LUT_SOLVER',
        'scattering_geometry_state':'SCATTERING_GEOMETRY_READY','scattering_angle_deg':angle,
    }])


def test_manifest_sha_and_calibration_provenance_are_required():
    df=full_grid(); b=df.to_csv(index=False).encode(); m=json.loads(manifest_bytes(b))
    m['csv_sha256']='0'*64
    a=validate_scattering_lut_bytes(b,json.dumps(m).encode())
    assert not a['ok']
    assert 'LUT_CSV_SHA256_MISMATCH' in a['errors']


def test_runtime_install_and_reload_roundtrip(tmp_path):
    df=full_grid(); b=df.to_csv(index=False).encode(); mb=manifest_bytes(b)
    a=install_scattering_lut(b,mb,tmp_path)
    assert a['ok']
    import os
    old_csv=os.environ.get('FIRECLOUD_TIER2_SCATTERING_LUT_PATH')
    old_man=os.environ.get('FIRECLOUD_TIER2_SCATTERING_LUT_MANIFEST_PATH')
    os.environ['FIRECLOUD_TIER2_SCATTERING_LUT_PATH']=str(tmp_path/'tier2_scattering_lut.csv')
    os.environ['FIRECLOUD_TIER2_SCATTERING_LUT_MANIFEST_PATH']=str(tmp_path/'tier2_scattering_lut_manifest.json')
    try:
        q,a2=load_installed_scattering_lut()
        assert a2['ok'] and len(q)==len(df)
        assert a2['calibration_id']=='CAL-001'
    finally:
        if old_csv is None: os.environ.pop('FIRECLOUD_TIER2_SCATTERING_LUT_PATH',None)
        else: os.environ['FIRECLOUD_TIER2_SCATTERING_LUT_PATH']=old_csv
        if old_man is None: os.environ.pop('FIRECLOUD_TIER2_SCATTERING_LUT_MANIFEST_PATH',None)
        else: os.environ['FIRECLOUD_TIER2_SCATTERING_LUT_MANIFEST_PATH']=old_man


def test_exact_target_requires_complete_local_4d_cell_at_all_six_bands():
    audit,lut=audit_and_lut()
    d=evaluate_tier2_scattering_domain(foundation=foundation(),readiness=readiness(),calibrated_lut=lut,lut_audit=audit)
    r=d.iloc[0]
    assert r.interpolation_domain_state=='INTERPOLATION_DOMAIN_READY_DETERMINISTIC'
    assert r.six_band_domain_ready_count==6
    assert bool(r.deterministic_interpolation_eligible)
    assert r.interpolation_executed == False
    s=summarize_tier2_scattering_domain(d).iloc[0]
    assert s.closure_state=='INTERPOLATION_DOMAIN_READY'


def test_range_inclusion_is_not_enough_if_local_cell_corner_is_missing():
    df=full_grid()
    # Remove one exact corner needed by the 600-nm local cell around the target.
    mask=(df.wavelength_nm==600)&(df.cot==1.0)&(df.effective_radius_um==8.0)&(df.cloud_thickness_km==0.5)&(df.scattering_angle_deg==60.0)
    df=df.loc[~mask].reset_index(drop=True)
    audit,lut=audit_and_lut(df)
    d=evaluate_tier2_scattering_domain(foundation=foundation(),readiness=readiness(),calibrated_lut=lut,lut_audit=audit)
    r=d.iloc[0]
    assert r.interpolation_domain_state=='LUT_LOCAL_CELL_INCOMPLETE'
    assert r.six_band_domain_ready_count==5
    assert '600nm:LOCAL_CELL_MISSING_CORNERS' in r.blocking_reason


def test_bounded_target_requires_both_cot_endpoints_inside_complete_domain():
    audit,lut=audit_and_lut()
    d=evaluate_tier2_scattering_domain(
        foundation=foundation(),readiness=readiness('BOUNDED_NATIVE_BRACKET','BOUNDED_INTERVAL',1.2,2.8),
        calibrated_lut=lut,lut_audit=audit,
    )
    r=d.iloc[0]
    assert r.interpolation_domain_state=='INTERPOLATION_DOMAIN_READY_BOUNDED'
    assert bool(r.bounded_interpolation_eligible)
    assert not bool(r.deterministic_interpolation_eligible)
    d2=evaluate_tier2_scattering_domain(
        foundation=foundation(),readiness=readiness('BOUNDED_NATIVE_BRACKET','BOUNDED_INTERVAL',0.5,2.8),
        calibrated_lut=lut,lut_audit=audit,
    )
    assert d2.iloc[0].interpolation_domain_state=='LUT_COT_OUT_OF_DOMAIN'


def test_out_of_domain_scattering_angle_is_explicit_not_clamped():
    audit,lut=audit_and_lut()
    d=evaluate_tier2_scattering_domain(foundation=foundation(140.0),readiness=readiness(),calibrated_lut=lut,lut_audit=audit)
    r=d.iloc[0]
    assert r.interpolation_domain_state=='LUT_SCATTERING_ANGLE_OUT_OF_DOMAIN'
    assert r.scattering_angle_domain_state=='SCATTERING_ANGLE_OUT_OF_DOMAIN'
