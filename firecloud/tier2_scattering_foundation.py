from __future__ import annotations
"""R5.7.18 Tier-2 scattering LUT / solver foundation.

This module freezes the solver boundary without inventing scattering physics.
It adds the physically required Sun→Cloud→Observer scattering angle and a
strict LUT schema/validator.  Production analysis remains blocked until a
calibrated LUT is explicitly installed and validated.
"""
import math
from dataclasses import dataclass
from typing import Iterable
import numpy as np
import pandas as pd

from .contracts import SIX_BAND_WAVELENGTHS_NM, CanvasCandidate
from .shared_geometry import scattering_angle_deg

SCATTERING_LUT_REQUIRED_COLUMNS = [
    "phase", "wavelength_nm", "cot", "effective_radius_um",
    "cloud_thickness_km", "scattering_angle_deg", "response_factor",
    "calibration_state", "lut_version",
]

TIER2_SCATTERING_FOUNDATION_COLUMNS = [
    "time","solar_altitude_deg","solar_azimuth_deg","canvas_id","cloud_layer_id",
    "operational_domain","distance_km","cloud_base_altitude_km",
    "tier2_input_contract_state","tier2_response_eligibility",
    "scattering_angle_deg","scattering_geometry_state",
    "scattering_lut_state","scattering_solver_state","solver_foundation_state",
    "deterministic_tier2_allowed","bounded_tier2_allowed",
    "blocking_reason","foundation_contract_version",
]

TIER2_SCATTERING_FOUNDATION_SUMMARY_COLUMNS = [
    "solar_altitude_deg","canvas_count","scattering_geometry_ready_count",
    "inputs_ready_geometry_ready_count","blocked_input_contract_count",
    "blocked_scattering_geometry_count","awaiting_calibrated_lut_count",
    "deterministic_tier2_allowed_count","bounded_tier2_allowed_count",
    "closure_state","foundation_contract_version",
]


def _finite(v) -> bool:
    try: return bool(math.isfinite(float(v)))
    except Exception: return False


def validate_scattering_lut(df: pd.DataFrame) -> dict:
    """Validate a candidate six-band target-cloud scattering LUT.

    Validation is deliberately strict.  It does not certify scientific
    calibration; it only certifies schema/domain integrity and that the caller
    explicitly marks rows CALIBRATED.
    """
    if df is None or df.empty:
        return {"valid":False,"state":"LUT_MISSING","reason":"EMPTY_LUT"}
    missing=[c for c in SCATTERING_LUT_REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        return {"valid":False,"state":"LUT_SCHEMA_INVALID","reason":"MISSING_COLUMNS:"+",".join(missing)}
    q=df.copy()
    for c in ["wavelength_nm","cot","effective_radius_um","cloud_thickness_km","scattering_angle_deg","response_factor"]:
        q[c]=pd.to_numeric(q[c],errors="coerce")
    if q[["wavelength_nm","cot","effective_radius_um","cloud_thickness_km","scattering_angle_deg","response_factor"]].isna().any().any():
        return {"valid":False,"state":"LUT_NUMERIC_INVALID","reason":"NON_NUMERIC_OR_NONFINITE"}
    if not q["wavelength_nm"].isin(list(SIX_BAND_WAVELENGTHS_NM)).all():
        return {"valid":False,"state":"LUT_WAVELENGTH_INVALID","reason":"OUTSIDE_FROZEN_SIX_BANDS"}
    if set(map(int,SIX_BAND_WAVELENGTHS_NM)) - set(q["wavelength_nm"].astype(int).unique()):
        return {"valid":False,"state":"LUT_WAVELENGTH_INCOMPLETE","reason":"MISSING_REQUIRED_WAVELENGTH"}
    if (q["cot"] < 0).any() or (q["effective_radius_um"] <= 0).any() or (q["cloud_thickness_km"] <= 0).any():
        return {"valid":False,"state":"LUT_DOMAIN_INVALID","reason":"NONPHYSICAL_GRID_COORDINATE"}
    if ((q["scattering_angle_deg"] < 0)|(q["scattering_angle_deg"] > 180)).any():
        return {"valid":False,"state":"LUT_DOMAIN_INVALID","reason":"SCATTERING_ANGLE_OUT_OF_RANGE"}
    if (q["response_factor"] < 0).any():
        return {"valid":False,"state":"LUT_RESPONSE_INVALID","reason":"NEGATIVE_RESPONSE_FACTOR"}
    if not q["calibration_state"].astype(str).str.upper().eq("CALIBRATED").all():
        return {"valid":False,"state":"LUT_NOT_CALIBRATED","reason":"CALIBRATION_STATE_NOT_CALIBRATED"}
    phases=set(q["phase"].astype(str).str.upper())
    if not phases.intersection({"LIQUID","WATER","ICE","MIXED"}):
        return {"valid":False,"state":"LUT_PHASE_INVALID","reason":"NO_SUPPORTED_PHASE"}
    versions=sorted(set(q["lut_version"].astype(str)))
    if len(versions) != 1:
        return {"valid":False,"state":"LUT_VERSION_MIXED","reason":"MULTIPLE_LUT_VERSIONS"}
    return {"valid":True,"state":"CALIBRATED_LUT_SCHEMA_READY","reason":"OK","lut_version":versions[0],"row_count":int(len(q))}


def build_tier2_scattering_foundation(
    *, readiness: pd.DataFrame, canvases: Iterable[CanvasCandidate],
    observer_lat_deg: float, observer_lon_deg: float, observer_alt_km: float,
    solar_altitude_deg: float, solar_azimuth_deg: float, valid_time=None,
    calibrated_lut: pd.DataFrame | None = None,
    lut_validation: dict | None = None,
) -> pd.DataFrame:
    canvases=list(canvases)
    if not canvases:
        return pd.DataFrame(columns=TIER2_SCATTERING_FOUNDATION_COLUMNS)
    cmap={str(c.canvas_id):c for c in canvases}
    rmap={}
    if readiness is not None and not readiness.empty:
        rmap={str(r.get("canvas_id")):r for _,r in readiness.iterrows()}
    if lut_validation is not None:
        lut_check = {
            "valid": bool(lut_validation.get("ok", False)),
            "state": str(lut_validation.get("state", "LUT_RUNTIME_INVALID")),
            "reason": ";".join(str(x) for x in lut_validation.get("errors", []) or []) or str(lut_validation.get("state", "UNKNOWN")),
        }
    else:
        lut_check=validate_scattering_lut(calibrated_lut) if calibrated_lut is not None else {"valid":False,"state":"CALIBRATED_LUT_NOT_INSTALLED","reason":"NO_CALIBRATED_LUT_INSTALLED"}
    rows=[]
    for cid,c in cmap.items():
        rr=rmap.get(cid)
        input_state=str(rr.get("tier2_input_contract_state","BLOCKED_INPUT_CONTRACT_MISSING")) if rr is not None else "BLOCKED_INPUT_CONTRACT_MISSING"
        response_elig=str(rr.get("tier2_response_eligibility","NOT_ELIGIBLE")) if rr is not None else "NOT_ELIGIBLE"
        try:
            angle=scattering_angle_deg(
                observer_lat_deg=observer_lat_deg,observer_lon_deg=observer_lon_deg,observer_alt_km=observer_alt_km,
                target_lat_deg=c.latitude,target_lon_deg=c.longitude,target_alt_km=c.cloud_base_altitude_km,
                solar_altitude_deg=solar_altitude_deg,solar_azimuth_deg=solar_azimuth_deg,
            )
            geom_state="SCATTERING_GEOMETRY_READY" if _finite(angle) else "SCATTERING_GEOMETRY_MISSING"
        except Exception:
            angle=np.nan; geom_state="SCATTERING_GEOMETRY_MISSING"
        inputs_ready=input_state == "INPUTS_READY_AWAITING_LUT_SOLVER"
        if not inputs_ready:
            foundation="BLOCKED_INPUT_CONTRACT"; reason=input_state
        elif geom_state != "SCATTERING_GEOMETRY_READY":
            foundation="BLOCKED_SCATTERING_GEOMETRY"; reason="SCATTERING_ANGLE_MISSING"
        elif not lut_check.get("valid",False):
            foundation="INPUTS_AND_GEOMETRY_READY_AWAITING_CALIBRATED_LUT"; reason=str(lut_check.get("reason"))
        else:
            foundation="FOUNDATION_READY_CALIBRATED_LUT_AVAILABLE"; reason="SOLVER_INTERPOLATION_NOT_ENABLED_IN_R5.7.18"
        truth=str(rr.get("target_optical_truth_state","")) if rr is not None else ""
        deterministic=bool(foundation=="FOUNDATION_READY_CALIBRATED_LUT_AVAILABLE" and truth.startswith("EXACT_"))
        bounded=bool(foundation=="FOUNDATION_READY_CALIBRATED_LUT_AVAILABLE" and truth=="BOUNDED_NATIVE_BRACKET")
        rows.append({
            "time":valid_time,"solar_altitude_deg":float(solar_altitude_deg),"solar_azimuth_deg":float(solar_azimuth_deg),
            "canvas_id":c.canvas_id,"cloud_layer_id":c.cloud_layer_id,"operational_domain":c.operational_domain.value,
            "distance_km":float(c.distance_km),"cloud_base_altitude_km":float(c.cloud_base_altitude_km),
            "tier2_input_contract_state":input_state,"tier2_response_eligibility":response_elig,
            "scattering_angle_deg":float(angle) if _finite(angle) else None,"scattering_geometry_state":geom_state,
            "scattering_lut_state":str(lut_check.get("state")),
            "scattering_solver_state":"FOUNDATION_SCHEMA_VALIDATOR_ONLY_NO_PRODUCTION_INTERPOLATION",
            "solver_foundation_state":foundation,"deterministic_tier2_allowed":deterministic,"bounded_tier2_allowed":bounded,
            "blocking_reason":reason,"foundation_contract_version":"R5.7.18_TIER2_SCATTERING_FOUNDATION_V1",
        })
    return pd.DataFrame(rows,columns=TIER2_SCATTERING_FOUNDATION_COLUMNS)


def summarize_tier2_scattering_foundation(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=TIER2_SCATTERING_FOUNDATION_SUMMARY_COLUMNS)
    rows=[]
    for a,g in df.groupby("solar_altitude_deg",sort=False):
        s=g["solver_foundation_state"].astype(str)
        geom=g["scattering_geometry_state"].astype(str).eq("SCATTERING_GEOMETRY_READY")
        n=len(g)
        awaiting=int(s.eq("INPUTS_AND_GEOMETRY_READY_AWAITING_CALIBRATED_LUT").sum())
        ready=int(s.eq("FOUNDATION_READY_CALIBRATED_LUT_AVAILABLE").sum())
        if n==0: closure="NOT_APPLICABLE"
        elif ready>0: closure="CALIBRATED_LUT_FOUNDATION_AVAILABLE"
        elif awaiting>0: closure="AWAITING_CALIBRATED_LUT"
        else: closure="INPUT_OR_GEOMETRY_BLOCKED"
        rows.append({
            "solar_altitude_deg":float(a),"canvas_count":int(n),"scattering_geometry_ready_count":int(geom.sum()),
            "inputs_ready_geometry_ready_count":int(((g["tier2_input_contract_state"].astype(str)=="INPUTS_READY_AWAITING_LUT_SOLVER") & geom).sum()),
            "blocked_input_contract_count":int(s.eq("BLOCKED_INPUT_CONTRACT").sum()),
            "blocked_scattering_geometry_count":int(s.eq("BLOCKED_SCATTERING_GEOMETRY").sum()),
            "awaiting_calibrated_lut_count":awaiting,
            "deterministic_tier2_allowed_count":int(g["deterministic_tier2_allowed"].fillna(False).astype(bool).sum()),
            "bounded_tier2_allowed_count":int(g["bounded_tier2_allowed"].fillna(False).astype(bool).sum()),
            "closure_state":closure,"foundation_contract_version":"R5.7.18_TIER2_SCATTERING_FOUNDATION_V1",
        })
    return pd.DataFrame(rows,columns=TIER2_SCATTERING_FOUNDATION_SUMMARY_COLUMNS)
