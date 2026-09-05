import numpy as np
import pandas as pd
from firecloud.spectral_rt import build_spectral_rt

def base():
    return pd.DataFrame([{"point_id":"p1","solar_altitude_deg":-2.0,"direction_offset_deg":0.0,"distance_km":20.0,"band":"0-40 km Primary Canvas","slant_cloud_optical_depth_estimate":0.2,"geometric_illuminated_fraction":1.0,"cloud_fraction_used":0.8}])

def test_missing_aod_never_becomes_default_clear_air():
    out=build_spectral_rt(base(),-2.0,aerosol_snapshot=pd.DataFrame(),angstrom_exponent=None)
    assert np.isnan(out.loc[0,"aod550"])
    assert np.isnan(out.loc[0,"aerosol_transmission_650nm"])
    assert np.isnan(out.loc[0,"partial_spectral_transmission_650nm"])

def test_real_aod_is_attached_but_angstrom_missing_is_explicit():
    aero=pd.DataFrame([{"point_id":"p1","aod550":0.23,"aerosol_provider":"OPEN_METEO_AIR_QUALITY_CAMS"}])
    out=build_spectral_rt(base(),-2.0,aerosol_snapshot=aero,angstrom_exponent=None)
    assert out.loc[0,"aod550"] == 0.23
    assert np.isnan(out.loc[0,"aerosol_transmission_650nm"])
    assert "ANGSTROM_MISSING" in out.loc[0,"spectral_rt_quality"]

def test_explicit_angstrom_enables_spectral_aerosol_rt():
    aero=pd.DataFrame([{"point_id":"p1","aod550":0.23,"aerosol_provider":"TEST"}])
    out=build_spectral_rt(base(),-2.0,aerosol_snapshot=aero,angstrom_exponent=1.2)
    assert out.loc[0,"aerosol_transmission_750nm"] > out.loc[0,"aerosol_transmission_600nm"]
