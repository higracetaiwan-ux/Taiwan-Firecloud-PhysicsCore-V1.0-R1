import io
import math

import pandas as pd
import pytest

from firecloud.shared_geometry import directional_scattering_geometry
from firecloud.tier2_directional_scattering_calibration import (
    DIRECTIONAL_CALIBRATION_CONTRACT,
    DIRECTIONAL_GEOMETRY_CONVENTION,
    DIRECTIONAL_INTERPOLATION_AXES,
    DIRECTIONAL_RESPONSE_DEFINITION,
    DIRECTIONAL_RESPONSE_UNITS,
    build_directional_calibration_jobs,
    build_directional_calibration_package,
    directional_scattering_angle_from_angles_deg,
    validate_directional_calibration_metadata,
    validate_directional_scattering_lut,
)
from firecloud.tier2_directional_scattering_runtime import validate_directional_lut_bytes
from firecloud.tier2_directional_scattering_domain import evaluate_tier2_directional_scattering_domain
from firecloud.tier2_directional_scattering_solver import (
    build_tier2_directional_scattering_response,
    interpolate_directional_response_factor,
    prepare_directional_scattering_lut,
)

WLS = [550, 575, 600, 650, 700, 750]


def formula(wl, cot, reff, theta0, thetav, relaz):
    return 0.01 + wl/100000.0 + 0.02*cot + 0.001*reff + 0.0002*theta0 + 0.0003*thetav + 0.0001*relaz


def samples():
    rows=[]
    for wl in WLS:
        for cot in [1.0,3.0]:
            for reff in [8.0,12.0]:
                for theta0 in [60.0,100.0]:
                    for thetav in [100.0,140.0]:
                        for relaz in [0.0,180.0]:
                            rows.append({
                                'phase':'LIQUID','wavelength_nm':wl,'cot':cot,'effective_radius_um':reff,
                                'solar_zenith_deg':theta0,'view_zenith_deg':thetav,'relative_azimuth_deg':relaz,
                                'response_factor':formula(wl,cot,reff,theta0,thetav,relaz),
                            })
    return pd.DataFrame(rows)


def metadata():
    return {
        'calibration_contract': DIRECTIONAL_CALIBRATION_CONTRACT,
        'calibration_state':'CALIBRATED','calibration_id':'DIR-PHYS-001',
        'calibration_source':'LIBRADTRAN_MYSTIC_VALIDATED_FULL_DIRECTIONAL_GRID',
        'calibration_date':'2026-09-08','qc_state':'PASS',
        'solver_family':'LIBRADTRAN_UVSPEC_MYSTIC','solver_version':'3.x-validated',
        'cloud_optics_source':'VALIDATED_MIE_WATER_TABLES',
        'phase_function_source':'VALIDATED_MIE_PHASE_MATRIX',
        'multiple_scattering_enabled':True,'response_definition':DIRECTIONAL_RESPONSE_DEFINITION,
        'response_units':DIRECTIONAL_RESPONSE_UNITS,'geometry_convention':DIRECTIONAL_GEOMETRY_CONVENTION,
        'directional_hemisphere_support':'FULL_0_180','validation_reference':'PHYSICAL_VALIDATION_REFERENCE',
        'lut_version':'DIRTEST22',
    }


def package():
    cb,mb,_=build_directional_calibration_package(samples(),metadata())
    audit=validate_directional_lut_bytes(cb,mb)
    assert audit['ok'], audit
    assert audit['solver_eligible'] is True
    return pd.read_csv(io.BytesIO(cb)), audit


def foundation(theta0=80.0,thetav=120.0,relaz=90.0):
    scat=directional_scattering_angle_from_angles_deg(theta0,thetav,relaz)
    return pd.DataFrame([{
        'time':'t','solar_altitude_deg':-2.0,'canvas_id':'c1','cloud_layer_id':'l1',
        'operational_domain':'PRIMARY_CANVAS_0_40','distance_km':20.0,
        'tier2_input_contract_state':'INPUTS_READY_AWAITING_LUT_SOLVER',
        'directional_geometry_state':'FULL_DIRECTIONAL_GEOMETRY_READY',
        'scattering_geometry_state':'SCATTERING_GEOMETRY_READY',
        'solar_zenith_deg':theta0,'view_zenith_deg':thetav,'relative_azimuth_deg':relaz,
        'scattering_angle_deg':scat,'solar_altitude_target_deg':90-theta0,'solar_azimuth_target_deg':270.0,
        'view_elevation_deg':90-thetav,'view_azimuth_target_deg':90.0,'mu0':math.cos(math.radians(theta0)),
        'mu_view':math.cos(math.radians(thetav)),'azimuth_degeneracy_state':'NONE',
    }])


def readiness():
    return pd.DataFrame([{
        'canvas_id':'c1','tier2_input_contract_state':'INPUTS_READY_AWAITING_LUT_SOLVER',
        'target_optical_truth_state':'EXACT_PRIMARY_NATIVE','target_cot_semantics':'EXACT_VALUE','phase':'LIQUID',
        'cot_lower_bound':2.0,'cot_upper_bound':2.0,'effective_radius_um':10.0,'cloud_thickness_km':1.2,
    }])


def illumination(v=2.0):
    r={'canvas_id':'c1'}
    for wl in WLS: r[f'relative_base_illumination_{wl}nm']=v
    return pd.DataFrame([r])


def test_directional_geometry_is_finite_and_scattering_diagnostic_closes_vector_identity():
    g=directional_scattering_geometry(
        observer_lat_deg=25.0,observer_lon_deg=121.0,observer_alt_km=0.0,
        target_lat_deg=25.0,target_lon_deg=121.3,target_alt_km=5.0,
        solar_altitude_deg=-2.0,solar_azimuth_deg=270.0,
    )
    assert 0 <= g.solar_zenith_deg <= 180
    assert 0 <= g.view_zenith_deg <= 180
    assert 0 <= g.relative_azimuth_deg <= 180
    assert 0 <= g.scattering_angle_deg <= 180
    derived=directional_scattering_angle_from_angles_deg(g.solar_zenith_deg,g.view_zenith_deg,g.relative_azimuth_deg)
    assert g.scattering_angle_deg == pytest.approx(derived, abs=1e-8)


def test_same_scattering_angle_does_not_collapse_full_directional_geometry():
    a=directional_scattering_angle_from_angles_deg(60,120,180)
    b=directional_scattering_angle_from_angles_deg(70,110,180)
    assert a == pytest.approx(0.0, abs=1e-10)
    assert b == pytest.approx(0.0, abs=1e-10)
    assert (60,120,180) != (70,110,180)


def test_directional_lut_rejects_legacy_scattering_angle_only_schema():
    legacy=pd.DataFrame([{
        'phase':'LIQUID','wavelength_nm':550,'cot':1,'effective_radius_um':10,
        'cloud_thickness_km':1,'scattering_angle_deg':90,'response_factor':0.2,
        'calibration_state':'CALIBRATED','lut_version':'LEGACY',
    }])
    a=validate_directional_scattering_lut(legacy)
    assert not a['valid']
    assert a['state']=='LEGACY_SCATTERING_ANGLE_LUT_NOT_DIRECTIONAL'


def test_production_directional_gate_requires_full_hemisphere_solver_not_plain_disort():
    m=metadata(); m['solver_family']='LIBRADTRAN_UVSPEC_DISORT'
    a=validate_directional_calibration_metadata(m)
    assert not a['ok']
    assert 'DIRECTIONAL_SOLVER_NOT_FULL_HEMISPHERE_APPROVED' in a['errors']


def test_directional_job_grid_has_three_angles_and_no_cloud_thickness_axis():
    spec={
        'phases':['LIQUID'],'wavelengths_nm':WLS,'cot':[1,3],'effective_radius_um':[10],
        'solar_zenith_deg':[80,100],'view_zenith_deg':[100,140],'relative_azimuth_deg':[0,180],
    }
    j=build_directional_calibration_jobs(spec,solver_family='LIBRADTRAN_UVSPEC_MYSTIC')
    assert len(j)==1*6*2*1*2*2*2
    assert 'scattering_angle_deg_diagnostic' in j.columns
    assert 'cloud_thickness_km' not in j.columns
    assert 'scattering_angle_deg' not in DIRECTIONAL_INTERPOLATION_AXES
    assert 'cloud_thickness_km' not in DIRECTIONAL_INTERPOLATION_AXES


def test_directional_package_and_runtime_production_gate_pass():
    lut,audit=package()
    assert len(lut)==len(samples())
    assert audit['geometry_convention']==DIRECTIONAL_GEOMETRY_CONVENTION
    assert audit['interpolation_axes']=='/'.join(DIRECTIONAL_INTERPOLATION_AXES)


def test_exact_target_requires_complete_local_5d_directional_cell_all_six_bands():
    lut,audit=package()
    d=evaluate_tier2_directional_scattering_domain(
        foundation=foundation(),readiness=readiness(),calibrated_lut=lut,lut_audit=audit,
    )
    r=d.iloc[0]
    assert r.interpolation_domain_state=='INTERPOLATION_DOMAIN_READY_DETERMINISTIC'
    assert r.six_band_domain_ready_count==6
    assert bool(r.deterministic_interpolation_eligible)
    assert r.scattering_angle_deg == pytest.approx(directional_scattering_angle_from_angles_deg(80,120,90))


def test_missing_directional_cell_corner_is_not_treated_as_complete():
    q=samples()
    mask=(q.wavelength_nm==600)&(q.cot==1)&(q.effective_radius_um==8)&(q.solar_zenith_deg==60)&(q.view_zenith_deg==100)&(q.relative_azimuth_deg==0)
    q=q.loc[~mask].reset_index(drop=True)
    with pytest.raises(ValueError,match='DIRECTIONAL_CALIBRATION_TENSOR_GRID_INCOMPLETE'):
        build_directional_calibration_package(q,metadata())


def test_directional_solver_reproduces_linear_5d_response_function():
    lut,audit=package()
    prepared=prepare_directional_scattering_lut(lut)
    for wl in WLS:
        got=interpolate_directional_response_factor(
            prepared,phase='LIQUID',wavelength_nm=wl,cot=2,effective_radius_um=10,
            solar_zenith_deg=80,view_zenith_deg=120,relative_azimuth_deg=90,
        )
        assert got==pytest.approx(formula(wl,2,10,80,120,90),abs=1e-12)
    domain=evaluate_tier2_directional_scattering_domain(
        foundation=foundation(),readiness=readiness(),calibrated_lut=lut,lut_audit=audit,
    )
    out=build_tier2_directional_scattering_response(
        domain=domain,calibrated_lut=lut,lut_audit=audit,cloud_base_illumination=illumination(),prepared_lut=prepared,
    )
    r=out.iloc[0]
    assert r.solver_execution_state=='EXECUTED_DETERMINISTIC'
    assert r.interpolation_mode=='DETERMINISTIC_5D_FULL_DIRECTIONAL_MULTILINEAR'
    for wl in WLS:
        assert r[f'response_factor_{wl}nm']==pytest.approx(formula(wl,2,10,80,120,90),abs=1e-12)
        assert r[f'tier2_radiance_{wl}nm']==pytest.approx(2*formula(wl,2,10,80,120,90),abs=1e-12)
