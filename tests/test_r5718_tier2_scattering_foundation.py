import math
import pandas as pd

from firecloud.contracts import CanvasCandidate, CanvasDomain, GeometryConfidence
from firecloud.shared_geometry import scattering_angle_deg
from firecloud.tier2_scattering_foundation import (
    validate_scattering_lut, build_tier2_scattering_foundation,
    summarize_tier2_scattering_foundation,
)


def canvas():
    return CanvasCandidate(
        canvas_id='c1', cloud_layer_id='l1', latitude=25.0, longitude=121.2,
        cloud_base_altitude_km=5.0, distance_km=30.0, azimuth_deg=270.0,
        operational_domain=CanvasDomain.PRIMARY_CANVAS_0_40, geometry_confidence=GeometryConfidence.HIGH,
    )


def readiness(state='INPUTS_READY_AWAITING_LUT_SOLVER', truth='EXACT_PRIMARY_NATIVE'):
    return pd.DataFrame([{
        'canvas_id':'c1','tier2_input_contract_state':state,
        'tier2_response_eligibility':'AWAITING_LUT_SOLVER',
        'target_optical_truth_state':truth,
    }])


def test_scattering_angle_is_finite_and_bounded():
    a=scattering_angle_deg(
        observer_lat_deg=25.0,observer_lon_deg=121.0,observer_alt_km=0.0,
        target_lat_deg=25.0,target_lon_deg=121.2,target_alt_km=5.0,
        solar_altitude_deg=-2.0,solar_azimuth_deg=270.0,
    )
    assert math.isfinite(a)
    assert 0.0 <= a <= 180.0


def test_foundation_does_not_enable_response_without_calibrated_lut():
    d=build_tier2_scattering_foundation(
        readiness=readiness(),canvases=[canvas()],observer_lat_deg=25.0,observer_lon_deg=121.0,observer_alt_km=0.0,
        solar_altitude_deg=-2.0,solar_azimuth_deg=270.0,calibrated_lut=None,
    )
    r=d.iloc[0]
    assert r.scattering_geometry_state == 'SCATTERING_GEOMETRY_READY'
    assert r.solver_foundation_state == 'INPUTS_AND_GEOMETRY_READY_AWAITING_CALIBRATED_LUT'
    assert r.scattering_lut_state == 'CALIBRATED_LUT_NOT_INSTALLED'
    assert not bool(r.deterministic_tier2_allowed)


def test_conflict_remains_blocked_before_lut():
    d=build_tier2_scattering_foundation(
        readiness=readiness('BLOCKED_COT_CONFLICT','DIRECT_EVIDENCE_CONFLICT'),canvases=[canvas()],
        observer_lat_deg=25.0,observer_lon_deg=121.0,observer_alt_km=0.0,
        solar_altitude_deg=-2.0,solar_azimuth_deg=270.0,
    )
    r=d.iloc[0]
    assert r.solver_foundation_state == 'BLOCKED_INPUT_CONTRACT'
    assert r.blocking_reason == 'BLOCKED_COT_CONFLICT'


def synthetic_lut(cal='CALIBRATED'):
    rows=[]
    for wl in [550,575,600,650,700,750]:
        rows.append({'phase':'LIQUID','wavelength_nm':wl,'cot':1.0,'effective_radius_um':10.0,
                     'cloud_thickness_km':1.0,'scattering_angle_deg':90.0,'response_factor':0.2,
                     'calibration_state':cal,'lut_version':'TEST1'})
    return pd.DataFrame(rows)


def test_lut_validator_requires_calibrated_six_band_contract():
    ok=validate_scattering_lut(synthetic_lut())
    assert ok['valid'] is True
    bad=validate_scattering_lut(synthetic_lut('EXPERIMENTAL'))
    assert bad['valid'] is False
    assert bad['state'] == 'LUT_NOT_CALIBRATED'


def test_calibrated_lut_only_opens_foundation_not_solver_interpolation():
    d=build_tier2_scattering_foundation(
        readiness=readiness(),canvases=[canvas()],observer_lat_deg=25.0,observer_lon_deg=121.0,observer_alt_km=0.0,
        solar_altitude_deg=-2.0,solar_azimuth_deg=270.0,calibrated_lut=synthetic_lut(),
    )
    r=d.iloc[0]
    assert r.solver_foundation_state == 'FOUNDATION_READY_CALIBRATED_LUT_AVAILABLE'
    assert bool(r.deterministic_tier2_allowed)
    assert r.scattering_solver_state == 'FOUNDATION_SCHEMA_VALIDATOR_ONLY_NO_PRODUCTION_INTERPOLATION'
    s=summarize_tier2_scattering_foundation(d).iloc[0]
    assert s.closure_state == 'CALIBRATED_LUT_FOUNDATION_AVAILABLE'
