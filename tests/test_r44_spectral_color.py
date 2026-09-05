import math
import pandas as pd

from firecloud.spectral_color import reconstruct_six_band_colour
from firecloud.optical_validation import build_cloud_optical_validation_table


def test_six_band_colour_fails_closed_when_550_missing():
    r={550:None,575:1,600:2,650:3,700:2,750:1}
    out=reconstruct_six_band_colour(r)
    assert out['spectral_colour_status']=='MISSING_SIX_BAND_RADIANCE'
    assert out['cie_x_truncated'] is None


def test_six_band_colour_uses_no_extra_blue_channel_and_returns_truncated_cie():
    r={550:0.1,575:0.2,600:0.6,650:1.0,700:0.8,750:0.3}
    out=reconstruct_six_band_colour(r)
    assert out['spectral_colour_status']=='READY_TRUNCATED_SIX_BAND_CIE_DIAGNOSTIC'
    assert 0 <= out['cie_x_truncated'] <= 1
    assert 0 <= out['cie_y_truncated'] <= 1
    assert 'NO_BLUE_EXTRAPOLATION' in out['colour_reconstruction_method']
    assert out['spectral_peak_wavelength_nm_diagnostic'] in r


def test_optical_validation_marks_missing_condensate_baseline():
    cl=pd.DataFrame([{'solar_altitude_deg':-2.0,'layer_id':'L1','optical_evidence':'GEOMETRY_ONLY','cot':float('nan')}])
    ca=pd.DataFrame([{'solar_altitude_deg':-2.0,'canvas_id':'C1','cloud_layer_id':'L1'}])
    hs=pd.DataFrame([{'solar_altitude_deg':-2.0,'horizontal_support_resolved':False}])
    ix=pd.DataFrame([{'solar_altitude_deg':-2.0,'slant_optics_status':'POTENTIAL_BLOCKER_HORIZONTAL_SUPPORT_UNKNOWN'}])
    out=build_cloud_optical_validation_table(cloud_layers=cl,canvases=ca,horizontal_support=hs,intersections=ix)
    assert out.iloc[0]['validation_state']=='NO_NATIVE_CONDENSATE_OPTICAL_EVIDENCE'
    assert out.iloc[0]['resolved_native_condensate_slant_intersection_count']==0


def test_optical_validation_detects_positive_slant_case():
    cl=pd.DataFrame([{'solar_altitude_deg':-2.0,'layer_id':'L1','optical_evidence':'PARTIAL_OPTICS','cot':1.4}])
    ca=pd.DataFrame([{'solar_altitude_deg':-2.0,'canvas_id':'C1','cloud_layer_id':'L1'}])
    hs=pd.DataFrame([{'solar_altitude_deg':-2.0,'horizontal_support_resolved':True}])
    ix=pd.DataFrame([{'solar_altitude_deg':-2.0,'slant_optics_status':'RESOLVED_NATIVE_CONDENSATE_SLANT_RT'}])
    out=build_cloud_optical_validation_table(cloud_layers=cl,canvases=ca,horizontal_support=hs,intersections=ix)
    assert out.iloc[0]['validation_state']=='CONDENSATE_POSITIVE_SLANT_RT_VALIDATED'
    assert out.iloc[0]['target_canvas_with_native_optics_count']==1
