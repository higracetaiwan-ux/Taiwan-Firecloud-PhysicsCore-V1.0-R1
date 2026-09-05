import pandas as pd
from firecloud.formation_gates import build_formation_gate_table

def test_gate_separates_geometry_from_unresolved_path():
    canv=pd.DataFrame([{'solar_altitude_deg':-2.0,'canvas_id':'c1','cloud_layer_id':'l1'}])
    ds=pd.DataFrame([{'canvas_id':'c1','direct_solar_fraction':0.7}])
    out=build_formation_gate_table(canv,ds,pd.DataFrame(),pd.DataFrame())
    assert out.iloc[0].cloud_exists
    assert out.iloc[0].cloud_receives_direct_solar_geometry
    assert out.iloc[0].formation_gate_state=='SUN_TO_CLOUDBASE_PATH_OPTICS_UNRESOLVED'
