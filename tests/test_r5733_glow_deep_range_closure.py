from types import SimpleNamespace

import numpy as np
import pandas as pd

import firecloud.twilight_glow as twilight_glow
from firecloud.case_integrity import build_analysis_integrity_audit
from firecloud.contracts import SIX_BAND_WAVELENGTHS_NM


def _profile_frame(min_z=0.075072):
    return pd.DataFrame({
        "altitude_agl_km": [min_z, 1.0, 5.0, 10.0],
        "temperature_k": [290.0, 284.0, 255.0, 225.0],
        "pressure_hpa": [1000.0, 900.0, 500.0, 250.0],
    })


def _fast_rec(min_z=0.075072):
    z=np.array([min_z,1.0,5.0,10.0],dtype=float)
    return {
        "z": z,
        "temperature_k": np.array([290.0,284.0,255.0,225.0]),
        "pressure_hpa": np.array([1000.0,900.0,500.0,250.0]),
        "o2_mole_fraction": np.array([0.20946]*4),
        "h2o_mole_fraction": np.array([0.01,0.006,0.001,0.0002]),
        "o3_mole_fraction": np.array([1.0e-8,2.0e-8,1.0e-7,4.0e-7]),
    }


def _target(z=3.75):
    return pd.Series({
        "time": "t0",
        "solar_altitude_deg": -5.5,
        "direction_offset_deg": 0.0,
        "target_distance_km": 100.0,
        "target_base_km": z-0.25,
        "target_top_km": z+0.25,
    })


def test_r5733_rayleigh_uses_only_frozen_lowest_native_profile_boundary_tolerance():
    profiles={float(d):_profile_frame() for d in np.arange(0.0,105.0,5.0)}
    tau,status,required,resolved=twilight_glow._rayleigh_observer_path(_target(),profiles,6371.0)
    assert status == "GLOW_OBSERVER_RAYLEIGH_PATH_RESOLVED"
    assert required == resolved > 0
    assert all(tau[int(w)] > 0.0 for w in SIX_BAND_WAVELENGTHS_NM)


def test_r5733_rayleigh_does_not_extrapolate_beyond_10m_native_boundary():
    profiles={float(d):_profile_frame(min_z=0.20) for d in np.arange(0.0,105.0,5.0)}
    _,status,required,resolved=twilight_glow._rayleigh_observer_path(_target(),profiles,6371.0)
    assert status == "GLOW_OBSERVER_RAYLEIGH_PATH_PARTIAL"
    assert resolved < required


def test_r5733_gas_species_uses_same_native_boundary_without_synthetic_state(monkeypatch):
    distances=np.arange(0.0,105.0,5.0)
    ctx=SimpleNamespace(
        valid=True,
        prepared_profile={0.0:{"distances":distances,"profiles":{float(d):_fast_rec() for d in distances}}},
        lut={},
    )
    monkeypatch.setattr(twilight_glow,"_sigma_fast",lambda *_a,**_k:1.0e-27)
    tau,status,required,resolved,path_km=twilight_glow._observer_gas_species_path(_target(),ctx,6371.0)
    assert status == "GLOW_OBSERVER_GAS_PATH_RESOLVED"
    assert required == resolved > 0
    assert path_km > 100.0
    assert all(tau[int(w)]["total"] > 0.0 for w in SIX_BAND_WAVELENGTHS_NM)


def test_r5733_gas_species_remains_partial_beyond_boundary_tolerance(monkeypatch):
    distances=np.arange(0.0,105.0,5.0)
    ctx=SimpleNamespace(
        valid=True,
        prepared_profile={0.0:{"distances":distances,"profiles":{float(d):_fast_rec(min_z=0.20) for d in distances}}},
        lut={},
    )
    monkeypatch.setattr(twilight_glow,"_sigma_fast",lambda *_a,**_k:1.0e-27)
    _,status,required,resolved,_=twilight_glow._observer_gas_species_path(_target(),ctx,6371.0)
    assert status == "GLOW_OBSERVER_GAS_PATH_PARTIAL"
    assert resolved < required


def test_r5733_cloud_conflict_is_explicitly_preserved_not_promoted_to_clear():
    cloud_layers=pd.DataFrame([
        {
            "time":"t0","solar_altitude_deg":-5.5,"direction_offset_deg":0.0,
            "layer_id":"L70","distance_km":70.0,"z_base_km":4.7444,"z_top_km":5.4776,
            "cloud_fraction":0.1,"cot":np.nan,"evidence_consistency":"CF_CLOUD_CONDENSATE_ZERO",
        },
        {
            "time":"t0","solar_altitude_deg":-5.5,"direction_offset_deg":0.0,
            "layer_id":"L80","distance_km":80.0,"z_base_km":4.7444,"z_top_km":5.4776,
            "cloud_fraction":0.0,"cot":0.0,"evidence_consistency":"CLEAR_CONSISTENT",
        },
    ])
    target=_target(z=7.75)
    diag=twilight_glow._observer_cloud_conflict_provenance(target,cloud_layers,pd.DataFrame(),6371.0)
    assert diag["state"] == "GLOW_OBSERVER_CLOUD_DIRECT_EVIDENCE_CONFLICT_PRESERVED"
    assert diag["unresolved_blocker_count"] >= 1
    assert diag["conflict_blocker_count"] == diag["unresolved_blocker_count"]
    assert "CF_CLOUD_CONDENSATE_ZERO" in diag["conflict_states"]


def _deep_observer_rows(*, molecular_resolved=True, promote_conflict=False):
    rows=[]
    for i,z in enumerate((3.75,7.75)):
        r={
            "time":"t0","solar_altitude_deg":-5.5,"direction_offset_deg":0.0,
            "distance_km":100.0,"scatter_altitude_km":z,"glow_volume_id":f"g{i}",
            "glow_observer_rayleigh_status": "GLOW_OBSERVER_RAYLEIGH_PATH_RESOLVED" if molecular_resolved else "GLOW_OBSERVER_RAYLEIGH_PATH_PARTIAL",
            "glow_observer_gas_species_status": "GLOW_OBSERVER_GAS_PATH_RESOLVED" if molecular_resolved else "GLOW_OBSERVER_GAS_PATH_PARTIAL",
            "glow_observer_cloud_evidence_state": "GLOW_OBSERVER_CLOUD_DIRECT_EVIDENCE_CONFLICT_PRESERVED" if z==7.75 else "GLOW_OBSERVER_CLOUD_PATH_CLEAR_DIAGNOSTIC",
            "glow_observer_cloud_unresolved_blocker_count": 1 if z==7.75 else 0,
            "glow_observer_cloud_conflict_blocker_count": 1 if z==7.75 else 0,
            "glow_observer_missing_components": "CLOUD" if z==7.75 else "",
        }
        for w in SIX_BAND_WAVELENGTHS_NM:
            r[f"glow_observer_tau_rayleigh_{int(w)}nm"] = 0.1
            r[f"glow_observer_tau_gas_non_o3_{int(w)}nm"] = 0.02
            r[f"glow_observer_tau_o3_{int(w)}nm"] = 0.01
            r[f"glow_observer_tau_cloud_{int(w)}nm"] = 0.0 if (promote_conflict and z==7.75) else np.nan if z==7.75 else 0.0
            r[f"glow_observer_band_evidence_state_{int(w)}nm"] = "FULL" if (promote_conflict and z==7.75) else "MISSING" if z==7.75 else "FULL"
        rows.append(r)
    return pd.DataFrame(rows)


def _integrity_status(observer):
    gas=pd.DataFrame({"temperature_k":[280.0,270.0],"pressure_hpa":[1000.0,900.0]})
    audit=build_analysis_integrity_audit({
        "gas_profile_route_snapshots":gas,
        "v1_twilight_glow_scatter_to_observer_extinction_550_750nm":observer,
        "twilight_glow_deep_range_closure_required":True,
    })
    return audit.set_index("check_id")["status"].to_dict()


def test_r5733_integrity_accepts_molecular_closure_and_preserved_cloud_conflict():
    checks=_integrity_status(_deep_observer_rows())
    assert checks["TWILIGHT_GLOW_OBSERVER_DEEP_RANGE_MOLECULAR_COVERAGE"] == "PASS"
    assert checks["TWILIGHT_GLOW_OBSERVER_CLOUD_CONFLICT_PRESERVATION"] == "PASS"


def test_r5741341_integrity_accepts_explicit_cloud_evidence_missing_without_tau_promotion():
    observer=_deep_observer_rows().copy()
    observer["glow_observer_cloud_evidence_state"]="GLOW_OBSERVER_CLOUD_EVIDENCE_MISSING"
    observer["glow_observer_missing_components"]="CLOUD"
    observer["glow_observer_cloud_unresolved_blocker_count"]=0
    observer["glow_observer_cloud_conflict_blocker_count"]=0
    for w in SIX_BAND_WAVELENGTHS_NM:
        observer[f"glow_observer_tau_cloud_{int(w)}nm"]=np.nan
        observer[f"glow_observer_band_evidence_state_{int(w)}nm"]="MISSING"
    checks=_integrity_status(observer)
    assert checks["TWILIGHT_GLOW_OBSERVER_CLOUD_CONFLICT_PRESERVATION"] == "PASS"


def test_r5733_integrity_rejects_unclosed_deep_range_molecular_path():
    checks=_integrity_status(_deep_observer_rows(molecular_resolved=False))
    assert checks["TWILIGHT_GLOW_OBSERVER_DEEP_RANGE_MOLECULAR_COVERAGE"] == "FAIL"


def test_r5733_integrity_rejects_missing_to_zero_cloud_conflict_promotion():
    checks=_integrity_status(_deep_observer_rows(promote_conflict=True))
    assert checks["TWILIGHT_GLOW_OBSERVER_CLOUD_CONFLICT_PRESERVATION"] == "FAIL"


def test_r57352_one_metre_boundary_precision_resolves_10378m_raw_gap_without_widening_10m_contract():
    """R5.7.35.2: 10.378 m raw gap rounds to exactly 10 m at 1 m native vertical precision."""
    profiles={float(d):_profile_frame(min_z=0.084998) for d in np.arange(0.0,105.0,5.0)}
    tau,status,required,resolved=twilight_glow._rayleigh_observer_path(_target(),profiles,6371.0)
    diag=twilight_glow._molecular_boundary_diagnostics(_target(),profiles,6371.0)
    assert status == "GLOW_OBSERVER_RAYLEIGH_PATH_RESOLVED"
    assert required == resolved > 0
    assert diag["snap_segment_count"] == 1
    assert 0.010 < diag["raw_max_gap_km"] < 0.0105
    assert abs(diag["quantized_max_gap_km"] - 0.010) < 1.0e-12
    assert all(tau[int(w)] > 0.0 for w in SIX_BAND_WAVELENGTHS_NM)


def test_r57352_one_metre_boundary_precision_still_fail_closes_true_11m_gap():
    """A true 11 m quantized gap remains outside the frozen 10 m allowance."""
    profiles={float(d):_profile_frame(min_z=0.0856) for d in np.arange(0.0,105.0,5.0)}
    _,status,required,resolved=twilight_glow._rayleigh_observer_path(_target(),profiles,6371.0)
    diag=twilight_glow._molecular_boundary_diagnostics(_target(),profiles,6371.0)
    assert status == "GLOW_OBSERVER_RAYLEIGH_PATH_PARTIAL"
    assert resolved < required
    assert diag["snap_segment_count"] == 0
    assert diag["quantized_max_gap_km"] > 0.010


def test_r57352_gas_species_uses_same_one_metre_boundary_precision(monkeypatch):
    distances=np.arange(0.0,105.0,5.0)
    ctx=SimpleNamespace(
        valid=True,
        prepared_profile={0.0:{"distances":distances,"profiles":{float(d):_fast_rec(min_z=0.084998) for d in distances}}},
        lut={},
    )
    monkeypatch.setattr(twilight_glow,"_sigma_fast",lambda *_a,**_k:1.0e-27)
    tau,status,required,resolved,path_km=twilight_glow._observer_gas_species_path(_target(),ctx,6371.0)
    assert status == "GLOW_OBSERVER_GAS_PATH_RESOLVED"
    assert required == resolved > 0
    assert path_km > 100.0
    assert all(tau[int(w)]["total"] > 0.0 for w in SIX_BAND_WAVELENGTHS_NM)
