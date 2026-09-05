import pandas as pd
from firecloud.formation_prerequisites import build_formation_prerequisite_table


def test_r46_prerequisites_fail_closed_for_missing_550_and_precip():
    sp=pd.DataFrame([
        {"solar_altitude_deg":-2.0,"canvas_id":"c1","wavelength_nm":wl,"tau_gas":(None if wl==550 else 0.1),"tau_precip":None,"evidence_state":"PARTIAL_OPTICS"}
        for wl in (550,575,600,650,700,750)
    ])
    cr=pd.DataFrame([{"solar_altitude_deg":-2.0,"canvas_id":"c1","target_optics_ready":True}])
    f=pd.DataFrame([{"solar_altitude_deg":-2.0,"formation_state":"UNCERTAIN_OPTICS"}])
    out=build_formation_prerequisite_table(spectral_paths=sp,canvas_radiance=cr,formation=f).iloc[0]
    assert out["formation_prerequisite_state"]=="FORMATION_PREREQUISITES_INCOMPLETE"
    assert "550NM_GAS_SPECTROSCOPY" in out["missing_prerequisites"]
    assert "PRECIPITATION_PATH_OPTICS" in out["missing_prerequisites"]


def test_r46_prerequisites_ready_only_with_real_full_inputs():
    rows=[]
    for wl in (550,575,600,650,700,750):
        rows.append({"solar_altitude_deg":-2.0,"canvas_id":"c1","wavelength_nm":wl,"tau_gas":0.1,"tau_precip":0.0,"evidence_state":"FULL"})
    out=build_formation_prerequisite_table(
        spectral_paths=pd.DataFrame(rows),
        canvas_radiance=pd.DataFrame([{"solar_altitude_deg":-2.0,"canvas_id":"c1","target_optics_ready":True}]),
        formation=pd.DataFrame([{"solar_altitude_deg":-2.0}]),
    ).iloc[0]
    assert out["formation_prerequisite_state"]=="READY_FOR_SIX_BAND_FORMATION"
