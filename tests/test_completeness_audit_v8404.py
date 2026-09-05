import pandas as pd
from firecloud.model import _build_physics_data_completeness


def test_full_rt_missing_is_not_base_forecast_zero():
    angle=-2.0
    details={angle:{
        "cams_native_aerosol_snapshot":pd.DataFrame(),
        "cams_native_aerosol_metadata":{},
        "gas_profile":pd.DataFrame({
            "temperature_k":[290.0],"pressure_hpa":[900.0],"relative_humidity_pct":[60.0],
            "h2o_mole_fraction":[0.01],"o2_mole_fraction":[0.20946],"o3_mole_fraction":[float('nan')]}),
        "hitran_backend_status":{"hapi_available":False,"database_exists":False},
        "spectral_voxels":pd.DataFrame({"full_spectral_transmission_600nm":[float('nan')],
            "full_spectral_transmission_650nm":[float('nan')],"full_spectral_transmission_700nm":[float('nan')],
            "full_spectral_transmission_750nm":[float('nan')]})}}
    summary=pd.DataFrame([{"solar_altitude_deg":angle,"data_completeness":1.0}])
    out=_build_physics_data_completeness(details,[(angle,pd.Timestamp('2026-09-03 18:20'),0.0)],summary)
    base=out[out.layer=="FORECAST_CLOUD"].iloc[0]
    full=out[out.layer=="FULL_SPECTRAL_RT"].iloc[0]
    gas=out[out.layer=="GAS_PROFILE"].iloc[0]
    assert base.status=="READY" and base.completeness==1.0
    assert full.status=="MISSING" and full.completeness==0.0
    assert gas.status=="PARTIAL" and gas.missing_reason=="O3_PROFILE_MISSING"
