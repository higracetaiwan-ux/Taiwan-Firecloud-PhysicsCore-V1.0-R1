import math
import pandas as pd

from firecloud.providers.cams_native import normalize_cams_geopotential_height_m
from firecloud.case_integrity import build_analysis_integrity_audit
from firecloud.contracts import SIX_BAND_WAVELENGTHS_NM


def _aerosol_payload(raw_heights=False):
    rows=[]
    for d in (0.0, 60.0, 80.0, 100.0):
        scale = 9.80665 if raw_heights else 1.0
        r={
            'time':'t0','solar_altitude_deg':-2.0,'direction_offset_deg':0.0,'distance_km':d,
            'cams_geopotential_height_normalization_state':'GEOPOTENTIAL_M2_S2_DIV_G0',
            'cams_geopotential_height_m_1000hPa':70.0*scale,
            'cams_geopotential_height_m_500hPa':5800.0*scale,
            'cams_geopotential_height_m_30hPa':24000.0*scale,
            'cams_native_aerosol_source':'CAMS_GLOBAL_FORECAST_NATIVE_3D_AEROSOL_EXTINCTION_532NM',
            'cams_aerext532_m1_1000hPa':1.0e-4,
        }
        for w in SIX_BAND_WAVELENGTHS_NM:
            r[f'aod{int(w)}']=0.2
        rows.append(r)
    return pd.DataFrame(rows)


def _glow_long_range(complete=True):
    rows=[]
    for d in (60.0,80.0,100.0):
        r={'time':'t0','solar_altitude_deg':-2.0,'direction_offset_deg':0.0,'distance_km':d,'glow_volume_id':f'g{int(d)}'}
        for w in SIX_BAND_WAVELENGTHS_NM:
            r[f'glow_observer_tau_aerosol_{int(w)}nm']=0.01 if complete else None
        rows.append(r)
    return pd.DataFrame(rows)


def _checks(aerosol, glow):
    audit=build_analysis_integrity_audit({
        'aerosol_spectral_route_snapshots':aerosol,
        'v1_twilight_glow_scatter_to_observer_extinction_550_750nm':glow,
        'cams_geopotential_normalization_required':True,
        'twilight_glow_observer_aerosol_coverage_required':True,
    })
    return audit.set_index('check_id')['status'].to_dict()


def test_ecmwf_geopotential_unit_spelling_is_divided_by_g0():
    h,state=normalize_cams_geopotential_height_m(236122.359375,'m**2 s**-2')
    assert state=='GEOPOTENTIAL_M2_S2_DIV_G0'
    assert math.isclose(h,236122.359375/9.80665,rel_tol=0,abs_tol=1e-9)


def test_unknown_geopotential_units_fail_closed():
    h,state=normalize_cams_geopotential_height_m(1234.0,'mystery-unit')
    assert math.isnan(h)
    assert state.startswith('CAMS_GEOPOTENTIAL_UNITS_UNRESOLVED')


def test_r5732_integrity_accepts_normalized_pressure_level_heights_and_long_range_aerosol():
    checks=_checks(_aerosol_payload(False),_glow_long_range(True))
    assert checks['CAMS_GEOPOTENTIAL_HEIGHT_NORMALIZATION']=='PASS'
    assert checks['TWILIGHT_GLOW_OBSERVER_AEROSOL_LONG_RANGE_COVERAGE']=='PASS'


def test_r5732_integrity_rejects_raw_geopotential_mislabelled_as_metres():
    checks=_checks(_aerosol_payload(True),_glow_long_range(True))
    assert checks['CAMS_GEOPOTENTIAL_HEIGHT_NORMALIZATION']=='FAIL'


def test_r5732_integrity_rejects_partial_long_range_aerosol_when_provider_ready():
    checks=_checks(_aerosol_payload(False),_glow_long_range(False))
    assert checks['TWILIGHT_GLOW_OBSERVER_AEROSOL_LONG_RANGE_COVERAGE']=='FAIL'

from firecloud.viewing_spectral import _integrate_view_aerosol


def _route_for_endpoint_test():
    rows=[]
    # Corrected CAMS geopotential-height levels: lowest native pressure surface
    # is 80 m AGL, while the long Glow observer-ray first midpoint is ~75 m.
    for d in (0.0,5.0,10.0,20.0,40.0,60.0,80.0,100.0):
        r={
            'distance_km':d,
            'spectral_aod_temporal_evidence_state':'EXACT_VALID_TIME',
            'spectral_aod_time_offset_hours':0.0,
            'spectral_aod_temporal_bound_hours':3.0,
            'aod550':0.2,
        }
        for w in SIX_BAND_WAVELENGTHS_NM:
            r[f'aod{int(w)}']=0.2
        # two or more native levels are enough for the interpolation helper.
        r['cams_geopotential_height_m_1000hPa']=80.0
        r['cams_aerext532_m1_1000hPa']=1.0e-4
        r['cams_geopotential_height_m_900hPa']=1000.0
        r['cams_aerext532_m1_900hPa']=8.0e-5
        r['cams_geopotential_height_m_500hPa']=5800.0
        r['cams_aerext532_m1_500hPa']=2.0e-5
        r['cams_geopotential_height_m_30hPa']=24000.0
        r['cams_aerext532_m1_30hPa']=1.0e-7
        rows.append(r)
    return pd.DataFrame(rows)


def test_glow_endpoint_snap_is_opt_in_and_does_not_weaken_default_viewing_contract():
    target=pd.Series({'target_distance_km':100.0,'target_base_km':3.5,'target_top_km':4.0})
    route=_route_for_endpoint_test()
    _,strict_status,_,strict_meta=_integrate_view_aerosol(target,route,6371.0)
    _,glow_status,_,glow_meta=_integrate_view_aerosol(target,route,6371.0,lowest_endpoint_tolerance_km=0.05)
    assert strict_status=='VIEW_AEROSOL_3D_PARTIAL'
    assert strict_meta['lowest_endpoint_snap_segment_count']==0
    assert glow_status=='VIEW_AEROSOL_3D_RESOLVED'
    assert glow_meta['lowest_endpoint_snap_segment_count']==1


def test_r57331_integrity_does_not_treat_spectral_aod_fallback_as_native_3d_ready():
    aerosol = pd.concat([_aerosol_payload(False), _aerosol_payload(False)], ignore_index=True)
    aerosol.loc[:3, 'time'] = 't0'
    aerosol.loc[:3, 'solar_altitude_deg'] = -2.0
    aerosol.loc[4:, 'time'] = 't1'
    aerosol.loc[4:, 'solar_altitude_deg'] = -5.5
    aerosol.loc[4:, 'cams_native_aerosol_source'] = None
    aerosol.loc[4:, 'cams_aerext532_m1_1000hPa'] = None
    for w in SIX_BAND_WAVELENGTHS_NM:
        aerosol.loc[4:, f'aod{int(w)}'] = 0.2
    aerosol.loc[4:, 'spectral_aod_temporal_evidence_state'] = 'REAL_ONE_SIDED_TEMPORAL_FALLBACK'

    glow0 = _glow_long_range(True)
    glow0['time'] = 't0'
    glow0['solar_altitude_deg'] = -2.0
    glow1 = _glow_long_range(False)
    glow1['time'] = 't1'
    glow1['solar_altitude_deg'] = -5.5
    glow = pd.concat([glow0, glow1], ignore_index=True)

    audit = build_analysis_integrity_audit({
        'aerosol_spectral_route_snapshots': aerosol,
        'v1_twilight_glow_scatter_to_observer_extinction_550_750nm': glow,
        'cams_geopotential_normalization_required': True,
        'twilight_glow_observer_aerosol_coverage_required': True,
    })
    row = audit[audit['check_id'].eq('TWILIGHT_GLOW_OBSERVER_AEROSOL_LONG_RANGE_COVERAGE')].iloc[0]
    assert row['status'] == 'PASS'
    assert 'resolved=3/3' in str(row['observed'])
    assert 'native_unavailable=3/6' in str(row['observed'])
