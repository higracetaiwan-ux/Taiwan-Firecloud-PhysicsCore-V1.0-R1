from pathlib import Path
import numpy as np
import pandas as pd

from firecloud.model import _build_physics_data_completeness


def _native_zero_voxels():
    rows=[]
    for d in (0.0, 20.0, 40.0, 60.0, 80.0, 100.0):
        for z in (0.25, 0.75, 1.25, 4.75, 8.25, 12.25):
            rows.append({
                "distance_km": d,
                "voxel_center_km": z,
                "native_microphysics_supported": True,
                "cloud_liquid_water_kgkg": 0.0,
                "cloud_ice_water_kgkg": 0.0,
            })
    return pd.DataFrame(rows)


def test_complete_zero_native_condensate_is_not_missing_and_target_rt_is_na():
    angle=-1.0
    details={angle:{
        "native_voxels": _native_zero_voxels(),
        "cams_native_aerosol_snapshot": pd.DataFrame(),
        "cams_native_aerosol_metadata": {},
        "gas_profile": pd.DataFrame(),
        "hitran_backend_status": {},
        "spectral_voxels": pd.DataFrame(),
    }}
    summary=pd.DataFrame([{"solar_altitude_deg":angle,"data_completeness":1.0}])
    formation=pd.DataFrame([{"solar_altitude_deg":angle,"formation_state":"NO_CANVAS_EVIDENCE"}])
    canvases=pd.DataFrame(columns=["solar_altitude_deg"])

    out=_build_physics_data_completeness(
        details, [(angle,pd.Timestamp("2026-09-07 18:12"),0.0)], summary,
        canvas_candidates=canvases, formation=formation,
    )

    native=out[out.layer.eq("NATIVE_CLOUD_CONDENSATE")].iloc[0]
    full=out[out.layer.eq("FULL_SPECTRAL_RT")].iloc[0]
    aero=out[out.layer.eq("SPECTRAL_AEROSOL_PATH")].iloc[0]

    assert native.status == "AVAILABLE_PHYSICALLY_ZERO"
    assert native.completeness == 1.0
    assert native.missing_reason == "NATIVE_CLWMR_ICMR_COMPLETE_ZERO_IN_0_100KM_CANVAS"
    assert full.status == "NOT_APPLICABLE"
    assert np.isnan(full.completeness)
    assert full.missing_reason == "NOT_APPLICABLE_NO_CANVAS_TARGET"
    assert aero.status == "NOT_APPLICABLE"
    assert np.isnan(aero.completeness)


def test_positive_native_condensate_is_ready_not_zero():
    angle=-1.0
    nv=_native_zero_voxels()
    nv.loc[nv.index[3], "cloud_ice_water_kgkg"] = 1e-5
    details={angle:{
        "native_voxels": nv,
        "cams_native_aerosol_snapshot": pd.DataFrame(),
        "cams_native_aerosol_metadata": {},
        "gas_profile": pd.DataFrame(),
        "hitran_backend_status": {},
        "spectral_voxels": pd.DataFrame({"distance_km":[20.0],"geometric_illuminated_fraction":[1.0]}),
    }}
    summary=pd.DataFrame([{"solar_altitude_deg":angle,"data_completeness":1.0}])
    canvases=pd.DataFrame([{"solar_altitude_deg":angle}])
    formation=pd.DataFrame([{"solar_altitude_deg":angle,"formation_state":"UNCERTAIN_OPTICS"}])
    out=_build_physics_data_completeness(
        details, [(angle,pd.Timestamp("2026-09-07 18:12"),0.0)], summary,
        canvas_candidates=canvases, formation=formation,
    )
    native=out[out.layer.eq("NATIVE_CLOUD_CONDENSATE")].iloc[0]
    assert native.status == "READY"
    assert native.completeness == 1.0


def test_ui_distinguishes_no_canvas_from_missing_native_condensate():
    text=(Path(__file__).resolve().parents[1]/"app.py").read_text(encoding="utf-8")
    assert "PHYSICALLY_ZERO ≠ MISSING" in text
    assert "Full Spectral RT：NOT APPLICABLE" in text
    assert "這是 NO_CANVAS_EVIDENCE，不是資料缺失" in text
