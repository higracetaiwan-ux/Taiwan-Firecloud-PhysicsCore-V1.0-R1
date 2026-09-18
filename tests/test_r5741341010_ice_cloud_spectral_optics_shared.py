import math
import numpy as np
import pandas as pd

import firecloud
from firecloud.ice_cloud_spectral_optics import (
    ICE_OPTICS_WAVELENGTHS_NM,
    IceOpticsLUTStatus,
    build_ice_cloud_spectral_optics_runtime,
    build_windy_ice_optics_summary,
    derive_mass_extinction_coefficient_m2_kg,
    ice_optics_contract_payload,
    normalize_tamu_isca_frame,
    summarize_ice_cloud_spectral_optics,
    validate_ice_optics_lut,
)
from firecloud.ice_optics_portable import portable_contract_payload


def _fake_lut():
    rows=[]
    for r, dmax in [(20.0,40.0),(40.0,80.0)]:
        for wl in ICE_OPTICS_WAVELENGTHS_NM:
            rows.append({
                'wavelength_nm':wl,
                'maximum_dimension_um':dmax,
                'effective_diameter_um':2*r,
                'effective_radius_um':r,
                'ice_habit':'8_columns',
                'surface_roughness':'Rough050',
                'mass_extinction_coefficient_m2_kg':100.0 + wl/1000.0 + r,
                'single_scattering_albedo':0.999,
                'asymmetry_parameter':0.75,
                'source_dataset':'TEST_CALIBRATED_LUT',
                'source_version':'v1',
                'source_record_provenance':'TEST',
            })
    return validate_ice_optics_lut(pd.DataFrame(rows))


def test_version_and_six_band_contract():
    assert firecloud.__version__ == '1.0.0-R5.7.41.3.4.10.30.8'
    assert ICE_OPTICS_WAVELENGTHS_NM == (550,575,600,650,700,750)


def test_mass_extinction_units_formula():
    # Qext=2, A/V=1 um^-1 -> 2e6/rho [m2/kg]
    got=derive_mass_extinction_coefficient_m2_kg(2.0, 10.0, 10.0)
    assert math.isclose(got, 2.0e6/917.0, rel_tol=1e-12)


def test_tamu_normalizer_derives_six_band_kext_without_fake_coefficients():
    # two spectral points bracket all requested bands; volume/area are fixed
    raw=pd.DataFrame([
        [0.50, 100.0, 1000.0, 100.0, 2.0, 0.99, 0.70],
        [0.80, 100.0, 1000.0, 100.0, 2.3, 0.995, 0.76],
    ], columns=['wavelength_um','maximum_dimension_um','volume_um3','projected_area_um2','extinction_efficiency','single_scattering_albedo','asymmetry_parameter'])
    out=normalize_tamu_isca_frame(raw, ice_habit='8_columns', surface_roughness='Rough050')
    assert tuple(out['wavelength_nm'].astype(int)) == ICE_OPTICS_WAVELENGTHS_NM
    assert (out['mass_extinction_coefficient_m2_kg'] > 0).all()
    assert out['source_record_provenance'].str.contains('WITHIN_SOURCE_GRID').all()
    # 1.5*V/A = 15 um Deff; Reff coordinate = 7.5 um
    assert np.allclose(out['effective_diameter_um'],15.0)
    assert np.allclose(out['effective_radius_um'],7.5)


def test_runtime_missing_semantics_and_tau_formula():
    lut=_fake_lut()
    native=pd.DataFrame([
        {
            'time':'2026-09-15T05:40:00+08:00','solar_altitude_deg':-2.0,'direction_offset_deg':0.0,'distance_km':20.0,
            'native_vertical_completeness':1.0,'ice_water_path_proxy_gm3_km':0.0,
        },
        {
            'time':'2026-09-15T05:40:00+08:00','solar_altitude_deg':-2.0,'direction_offset_deg':0.0,'distance_km':60.0,
            'native_vertical_completeness':1.0,'ice_water_path_proxy_gm3_km':0.02,
            'ice_maximum_dimension_um':60.0,'ice_effective_radius_um':30.0,'ice_habit':'8_columns','ice_surface_roughness':'Rough050',
        },
        {
            'time':'2026-09-15T05:40:00+08:00','solar_altitude_deg':-2.0,'direction_offset_deg':5.0,'distance_km':80.0,
            'native_vertical_completeness':0.5,'ice_water_path_proxy_gm3_km':0.03,
            'ice_maximum_dimension_um':60.0,'ice_effective_radius_um':30.0,'ice_habit':'8_columns','ice_surface_roughness':'Rough050',
        },
    ])
    status=IceOpticsLUTStatus(True,'test.csv',len(lut),True,'ICE_OPTICS_LUT_READY')
    rt=build_ice_cloud_spectral_optics_runtime(native,lut=lut,lut_status=status)
    assert rt.iloc[0]['ice_optics_state']=='NO_ICE_CONDENSATE_AT_NATIVE_STATE'
    for wl in ICE_OPTICS_WAVELENGTHS_NM:
        assert rt.iloc[0][f'tau_ice_{wl}']==0.0
        assert rt.iloc[0][f'ice_transmission_{wl}']==1.0
    assert rt.iloc[1]['ice_optics_state']=='ICE_SIX_BAND_OPTICS_READY'
    for wl in ICE_OPTICS_WAVELENGTHS_NM:
        assert math.isclose(rt.iloc[1][f'tau_ice_{wl}'], rt.iloc[1]['native_iwp_kg_m2']*rt.iloc[1][f'k_ext_ice_{wl}_m2_kg'], rel_tol=1e-12)
    assert rt.iloc[2]['ice_optics_state']=='ICE_IWP_INCOMPLETE_NATIVE_VERTICAL_SUPPORT'
    assert all(pd.isna(rt.iloc[2][f'tau_ice_{wl}']) for wl in ICE_OPTICS_WAVELENGTHS_NM)
    assert not rt['tau_synthesis_allowed'].any()
    assert not rt['formation_promotion_allowed'].any()



def test_positive_iwp_with_reff_but_without_dmax_fails_closed_no_reff_substitution():
    lut=_fake_lut()
    native=pd.DataFrame([{
        'solar_altitude_deg':-2.0,'direction_offset_deg':0.0,'distance_km':60.0,
        'native_vertical_completeness':1.0,'ice_water_path_proxy_gm3_km':0.02,
        'ice_effective_radius_um':30.0,'ice_habit':'8_columns','ice_surface_roughness':'Rough050',
    }])
    status=IceOpticsLUTStatus(True,'test.csv',len(lut),True,'ICE_OPTICS_LUT_READY')
    rt=build_ice_cloud_spectral_optics_runtime(native,lut=lut,lut_status=status)
    assert rt.iloc[0]['ice_optics_state']=='ICE_MAXIMUM_DIMENSION_MISSING'
    assert rt.iloc[0]['ice_optics_missing_reason']=='NO_NATIVE_OR_CALIBRATED_ICE_DMAX'
    assert pd.isna(rt.iloc[0]['ice_maximum_dimension_um'])
    assert rt.iloc[0]['ice_effective_radius_um']==30.0
    assert all(pd.isna(rt.iloc[0][f'tau_ice_{wl}']) for wl in ICE_OPTICS_WAVELENGTHS_NM)


def test_dmax_lookup_is_cross_band_stable_when_source_reff_is_wavelength_dependent():
    rows=[]
    for dmax,scale in [(40.0,1.0),(80.0,2.0)]:
        for idx,wl in enumerate(ICE_OPTICS_WAVELENGTHS_NM):
            rows.append({
                'wavelength_nm':wl,
                'maximum_dimension_um':dmax,
                'effective_diameter_um':10.0*scale + idx,
                'effective_radius_um':5.0*scale + idx*0.5,
                'ice_habit':'HBR',
                'surface_roughness':'Rough000',
                'mass_extinction_coefficient_m2_kg':100.0*scale + idx,
                'single_scattering_albedo':0.999,
                'asymmetry_parameter':0.75,
                'source_dataset':'TEST_WAVELENGTH_DEPENDENT_REFF',
                'source_version':'v1',
                'source_record_provenance':'TEST',
            })
    lut=validate_ice_optics_lut(pd.DataFrame(rows))
    native=pd.DataFrame([{
        'solar_altitude_deg':-2.0,'direction_offset_deg':0.0,'distance_km':60.0,
        'native_vertical_completeness':1.0,'ice_water_path_proxy_gm3_km':0.01,
        'ice_maximum_dimension_um':60.0,'ice_effective_radius_um':999.0,
        'ice_habit':'HBR','ice_surface_roughness':'Rough000',
    }])
    status=IceOpticsLUTStatus(True,'test.csv',len(lut),True,'ICE_OPTICS_LUT_READY')
    rt=build_ice_cloud_spectral_optics_runtime(native,lut=lut,lut_status=status)
    assert rt.iloc[0]['ice_optics_state']=='ICE_SIX_BAND_OPTICS_READY'
    assert rt.iloc[0]['ice_optics_lookup_state']=='LINEAR_DMAX_INTERPOLATION_WITHIN_LUT'
    assert rt.iloc[0]['ice_maximum_dimension_um']==60.0
    # Deliberately nonsensical r_eff is preserved only as metadata and cannot alter lookup.
    assert rt.iloc[0]['ice_effective_radius_um']==999.0
    assert all(pd.notna(rt.iloc[0][f'tau_ice_{wl}']) for wl in ICE_OPTICS_WAVELENGTHS_NM)


def test_no_lut_positive_iwp_fail_closes():
    native=pd.DataFrame([{
        'solar_altitude_deg':-2.0,'direction_offset_deg':0.0,'distance_km':60.0,
        'native_vertical_completeness':1.0,'ice_water_path_proxy_gm3_km':0.02,
        'ice_maximum_dimension_um':60.0,'ice_effective_radius_um':30.0,'ice_habit':'8_columns','ice_surface_roughness':'Rough050',
    }])
    status=IceOpticsLUTStatus(False,None,0,False,'ICE_OPTICS_LUT_NOT_CONFIGURED')
    rt=build_ice_cloud_spectral_optics_runtime(native,lut=pd.DataFrame(columns=[
        'wavelength_nm','maximum_dimension_um','effective_diameter_um','effective_radius_um','ice_habit','surface_roughness',
        'mass_extinction_coefficient_m2_kg','single_scattering_albedo','asymmetry_parameter','source_dataset','source_version','source_record_provenance'
    ]),lut_status=status)
    assert rt.iloc[0]['ice_optics_state']=='ICE_OPTICS_LUT_UNAVAILABLE'
    assert all(pd.isna(rt.iloc[0][f'tau_ice_{wl}']) for wl in ICE_OPTICS_WAVELENGTHS_NM)


def test_windy_export_contract_is_compact_and_non_promoting():
    lut=_fake_lut(); status=IceOpticsLUTStatus(True,'test.csv',len(lut),True,'ICE_OPTICS_LUT_READY')
    native=pd.DataFrame([{
        'time':'2026-09-15T05:40:00+08:00','solar_altitude_deg':-2.0,'direction_offset_deg':0.0,'distance_km':60.0,
        'native_vertical_completeness':1.0,'ice_water_path_proxy_gm3_km':0.02,
        'ice_maximum_dimension_um':60.0,'ice_effective_radius_um':30.0,'ice_habit':'8_columns','ice_surface_roughness':'Rough050',
    }])
    rt=build_ice_cloud_spectral_optics_runtime(native,lut=lut,lut_status=status)
    summary=summarize_ice_cloud_spectral_optics(rt)
    frame,payload=build_windy_ice_optics_summary(summary,physicscore_version=firecloud.__version__,science_baseline='R5.7.41.2_SHADOW_COT_AB_FROZEN',lut_status=status)
    assert payload['ice_optics_contract_version']=='FIRECLOUD_ICE_OPTICS_V1'
    assert payload['wavelengths_nm']==list(ICE_OPTICS_WAVELENGTHS_NM)
    assert payload['primary_size_coordinate']=='maximum_dimension_um'
    assert payload['physics_promotion_allowed'] is False
    assert len(payload['records'])==1
    assert frame.iloc[0]['distance_band']=='40-100km_EXTENDED_CANVAS'


def test_contract_payload_freezes_missing_semantics():
    c=ice_optics_contract_payload(physicscore_version=firecloud.__version__,science_baseline='R5.7.41.2_SHADOW_COT_AB_FROZEN')
    assert c['wavelengths_nm']==list(ICE_OPTICS_WAVELENGTHS_NM)
    assert 'Missing != Clear != Zero' in c['missing_semantics']
    assert 'tau_ice_lambda = IWP_kg_m2 * k_ext_ice_lambda_m2_kg' == c['tau_definition']
    assert c['primary_size_coordinate']=='maximum_dimension_um'
    assert 'r_eff-to-Dmax' in c['missing_semantics']

def test_analysis_integrity_guards_ice_optics_and_windy_contract():
    from firecloud.case_integrity import build_analysis_integrity_audit
    lut=_fake_lut(); status=IceOpticsLUTStatus(True,'test.csv',len(lut),True,'ICE_OPTICS_LUT_READY')
    native=pd.DataFrame([{
        'time':'2026-09-15T05:40:00+08:00','solar_altitude_deg':-2.0,'direction_offset_deg':0.0,'distance_km':60.0,
        'native_vertical_completeness':1.0,'ice_water_path_proxy_gm3_km':0.02,
        'ice_maximum_dimension_um':60.0,'ice_effective_radius_um':30.0,'ice_habit':'8_columns','ice_surface_roughness':'Rough050',
    }])
    rt=build_ice_cloud_spectral_optics_runtime(native,lut=lut,lut_status=status)
    sm=summarize_ice_cloud_spectral_optics(rt)
    wf,wj=build_windy_ice_optics_summary(sm,physicscore_version=firecloud.__version__,science_baseline='R5.7.41.2_SHADOW_COT_AB_FROZEN',lut_status=status)
    contract=ice_optics_contract_payload(physicscore_version=firecloud.__version__,science_baseline='R5.7.41.2_SHADOW_COT_AB_FROZEN')
    audit=build_analysis_integrity_audit({
        'v1_ice_cloud_spectral_optics_runtime':rt,
        'v1_ice_cloud_spectral_optics_summary':sm,
        'v1_windy_ice_optics_summary':wf,
        'windy_firecloud_ice_optics_summary_v1':wj,
        'ice_cloud_spectral_optics_contract':contract,
        'ice_optics_portable_consumer_contract':portable_contract_payload(physicscore_version=firecloud.__version__,science_baseline='R5.7.41.2_SHADOW_COT_AB_FROZEN'),
        'ice_cloud_spectral_optics_phase1_required':True,
    })
    checks=audit.set_index('check_id')['status'].to_dict()
    assert checks['ICE_CLOUD_SPECTRAL_OPTICS_SIX_BAND_CONTRACT']=='PASS'
    assert checks['ICE_CLOUD_SPECTRAL_OPTICS_ROLE_SEPARATION']=='PASS'
    assert checks['ICE_CLOUD_SPECTRAL_OPTICS_MISSING_SEMANTICS']=='PASS'
    assert checks['WINDY_ICE_OPTICS_EXPORT_CONTRACT']=='PASS'
