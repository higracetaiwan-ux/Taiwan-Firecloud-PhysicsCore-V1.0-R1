import math
import numpy as np
import pandas as pd
from firecloud.spectral_rt import rayleigh_vertical_optical_depth, aerosol_optical_depth, build_spectral_rt

def test_rayleigh_decreases_with_wavelength():
    vals=[rayleigh_vertical_optical_depth(w) for w in (600,650,700,750)]
    assert vals == sorted(vals, reverse=True)

def test_angstrom_aod_decreases_for_positive_exponent():
    vals=[aerosol_optical_depth(w,0.2,1.3) for w in (600,650,700,750)]
    assert vals == sorted(vals, reverse=True)

def test_spectral_rt_keeps_gas_missing_and_partial_available():
    df=pd.DataFrame([{ "point_id":"p1","solar_altitude_deg":-2.0,"direction_offset_deg":0.0,"distance_km":20.0,"band":"0-40 km Primary Canvas","slant_cloud_optical_depth_estimate":0.5,"geometric_illuminated_fraction":1.0,"cloud_fraction_used":0.8 }])
    out=build_spectral_rt(df,-2.0,aerosol_snapshot=pd.DataFrame([{"point_id":"p1","aod550":0.12,"aerosol_provider":"TEST"}]),angstrom_exponent=1.3)
    assert not np.isnan(out.loc[0,"partial_spectral_transmission_650nm"])
    assert np.isnan(out.loc[0,"full_spectral_transmission_650nm"])
    assert out.loc[0,"gas_status_650nm"] == "HITRAN_LOCAL_BAND_TABLE_MISSING"

def test_partial_red_transmission_is_spectrally_resolved():
    df=pd.DataFrame([{ "point_id":"p1","solar_altitude_deg":-3.0,"direction_offset_deg":0.0,"distance_km":40.0,"band":"0-40 km Primary Canvas","slant_cloud_optical_depth_estimate":0.2,"geometric_illuminated_fraction":1.0,"cloud_fraction_used":1.0 }])
    out=build_spectral_rt(df,-3.0,aerosol_snapshot=pd.DataFrame([{"point_id":"p1","aod550":0.12,"aerosol_provider":"TEST"}]),angstrom_exponent=1.3)
    assert out.loc[0,"partial_spectral_transmission_750nm"] > out.loc[0,"partial_spectral_transmission_600nm"]
