"""Tier-2 target-cloud scattering readiness contract.

R5.7.17 is an evidence/readiness layer only.  It does not run a scattering
solver and it does not create COT, phase, effective radius, or cloud thickness
from CF/RH/geometry heuristics.
"""
from __future__ import annotations

import math
from typing import Iterable
import pandas as pd
import numpy as np

from .contracts import SIX_BAND_WAVELENGTHS_NM, CloudScene, CanvasCandidate

TIER2_SCATTERING_READINESS_COLUMNS = [
    "time", "solar_altitude_deg", "canvas_id", "cloud_layer_id",
    "operational_domain", "distance_km", "cloud_base_altitude_km",
    "target_optical_truth_state", "target_cot_semantics", "target_response_eligibility",
    "cot_readiness_state", "cot_exact_or_bounded", "cot_lower_bound", "cot_upper_bound",
    "phase", "phase_readiness_state", "effective_radius_um", "reff_readiness_state",
    "cloud_thickness_km", "thickness_readiness_state",
    "six_band_incident_readiness_state", "six_band_incident_ready_count",
    "required_wavelength_count", "required_wavelengths_nm",
    "tier2_input_completeness_fraction", "tier2_input_contract_state",
    "scattering_lut_state", "scattering_solver_state", "tier2_response_eligibility",
    "blocking_reason", "cf_or_rh_used_to_infer_cot", "tier2_contract_version",
]

TIER2_SCATTERING_READINESS_SUMMARY_COLUMNS = [
    "solar_altitude_deg", "canvas_count", "inputs_ready_count",
    "blocked_cot_conflict_count", "blocked_cot_missing_count",
    "blocked_phase_count", "blocked_reff_count", "blocked_thickness_count",
    "blocked_six_band_count", "awaiting_lut_solver_count", "response_ready_count",
    "mean_input_completeness_fraction", "closure_state", "tier2_contract_version",
]


def _finite(v) -> bool:
    try:
        return bool(math.isfinite(float(v)))
    except Exception:
        return False


def _truth_cot_state(truth: str, semantics: str) -> tuple[str, bool]:
    truth = str(truth or "OPTICS_UNKNOWN")
    semantics = str(semantics or "UNRESOLVED_MISSING")
    if truth.startswith("EXACT_") and semantics == "EXACT_VALUE":
        return "COT_EXACT_READY", True
    if truth == "BOUNDED_NATIVE_BRACKET" and semantics == "BOUNDED_INTERVAL":
        return "COT_BOUNDED_READY", True
    if truth in {"DIRECT_EVIDENCE_CONFLICT", "MULTISOURCE_DISAGREEMENT"} or semantics == "UNRESOLVED_CONFLICT":
        return "COT_CONFLICT_UNRESOLVED", False
    if truth == "NO_TARGET_CLOUD_GEOMETRY" or semantics == "NOT_APPLICABLE":
        return "COT_NOT_APPLICABLE_NO_TARGET", False
    return "COT_MISSING_OR_UNKNOWN", False


def _incident_ready(row: pd.Series | None) -> tuple[str, int]:
    if row is None:
        return "SIX_BAND_INCIDENT_MISSING", 0
    count = 0
    for wl in SIX_BAND_WAVELENGTHS_NM:
        # Prefer the actual cloud-base irradiance contract.  Fall back to the
        # Tier-1 response interval only as evidence that the six-band incident
        # branch was present; no scattering physics is inferred here.
        names = [
            f"relative_base_illumination_{int(wl)}nm",
            f"cloud_radiance_proxy_{int(wl)}nm",
            f"cloud_radiance_proxy_{int(wl)}nm_lower_bound",
        ]
        if any(name in row.index and _finite(row.get(name, np.nan)) for name in names):
            count += 1
    if count == len(SIX_BAND_WAVELENGTHS_NM):
        return "SIX_BAND_INCIDENT_READY", count
    if count > 0:
        return "SIX_BAND_INCIDENT_PARTIAL", count
    return "SIX_BAND_INCIDENT_MISSING", 0


def build_tier2_scattering_readiness(
    *, scene: CloudScene, canvases: Iterable[CanvasCandidate],
    target_optical_evidence: pd.DataFrame, canvas_radiance: pd.DataFrame,
    cloud_base_illumination: pd.DataFrame, solar_altitude_deg: float, valid_time=None,
) -> pd.DataFrame:
    canvases = list(canvases)
    if not canvases:
        return pd.DataFrame(columns=TIER2_SCATTERING_READINESS_COLUMNS)
    layers = {x.layer_id: x for x in scene.layers}
    evmap = {}
    if target_optical_evidence is not None and not target_optical_evidence.empty:
        evmap = {str(r.get("canvas_id")): r for _, r in target_optical_evidence.iterrows()}
    radmap = {}
    if canvas_radiance is not None and not canvas_radiance.empty:
        radmap = {str(r.get("canvas_id")): r for _, r in canvas_radiance.iterrows()}
    illumap = {}
    if cloud_base_illumination is not None and not cloud_base_illumination.empty:
        illumap = {str(r.get("canvas_id")): r for _, r in cloud_base_illumination.iterrows()}

    rows=[]
    for canvas in canvases:
        layer = layers.get(canvas.cloud_layer_id)
        ev = evmap.get(str(canvas.canvas_id))
        rad = radmap.get(str(canvas.canvas_id))
        il = illumap.get(str(canvas.canvas_id))
        truth = str(ev.get("target_optical_truth_state", "OPTICS_UNKNOWN")) if ev is not None else "OPTICS_UNKNOWN"
        semantics = str(ev.get("target_cot_semantics", "UNRESOLVED_MISSING")) if ev is not None else "UNRESOLVED_MISSING"
        eligibility = str(ev.get("target_response_eligibility", "NO_EXACT_RESPONSE")) if ev is not None else "NO_EXACT_RESPONSE"
        cot_state, cot_ok = _truth_cot_state(truth, semantics)
        cot_lo = ev.get("target_cot_lower_bound", np.nan) if ev is not None else np.nan
        cot_hi = ev.get("target_cot_upper_bound", np.nan) if ev is not None else np.nan
        phase = str(getattr(layer, "phase", "UNKNOWN") or "UNKNOWN") if layer is not None else "UNKNOWN"
        phase_ok = phase.upper() not in {"", "UNKNOWN", "NONE"}
        reff = getattr(layer, "effective_radius_um", None) if layer is not None else None
        reff_ok = _finite(reff) and float(reff) > 0.0
        thickness = (float(layer.z_top_km)-float(layer.z_base_km)) if layer is not None and _finite(layer.z_top_km) and _finite(layer.z_base_km) else None
        thickness_ok = _finite(thickness) and float(thickness) > 0.0
        incident_row = il if il is not None else rad
        incident_state, incident_count = _incident_ready(incident_row)
        incident_ok = incident_count == len(SIX_BAND_WAVELENGTHS_NM)
        flags=[cot_ok, phase_ok, reff_ok, thickness_ok, incident_ok]
        completeness=float(sum(bool(x) for x in flags)/len(flags))

        if not cot_ok:
            if cot_state == "COT_CONFLICT_UNRESOLVED":
                contract="BLOCKED_COT_CONFLICT"; reason="TARGET_COT_CONFLICT_UNRESOLVED"
            elif cot_state == "COT_NOT_APPLICABLE_NO_TARGET":
                contract="NOT_APPLICABLE_NO_TARGET"; reason="NO_TARGET_CLOUD_GEOMETRY"
            else:
                contract="BLOCKED_COT_MISSING"; reason="TARGET_COT_MISSING_OR_UNKNOWN"
        elif not phase_ok:
            contract="BLOCKED_PHASE_MISSING"; reason="TARGET_PHASE_MISSING"
        elif not reff_ok:
            contract="BLOCKED_REFF_MISSING"; reason="TARGET_EFFECTIVE_RADIUS_MISSING"
        elif not thickness_ok:
            contract="BLOCKED_THICKNESS_MISSING"; reason="TARGET_CLOUD_THICKNESS_MISSING"
        elif not incident_ok:
            contract="BLOCKED_SIX_BAND_INCIDENT_INCOMPLETE"; reason=incident_state
        else:
            contract="INPUTS_READY_AWAITING_LUT_SOLVER"; reason="NONE_INPUTS_COMPLETE"

        # R5.7.17 intentionally has no calibrated Tier-2 LUT/solver.
        lut_state="TIER2_SCATTERING_LUT_NOT_FROZEN"
        solver_state="TIER2_SCATTERING_SOLVER_NOT_ENABLED"
        response_eligibility=("AWAITING_LUT_SOLVER" if contract == "INPUTS_READY_AWAITING_LUT_SOLVER" else "NOT_ELIGIBLE")
        rows.append({
            "time":valid_time, "solar_altitude_deg":float(solar_altitude_deg),
            "canvas_id":canvas.canvas_id, "cloud_layer_id":canvas.cloud_layer_id,
            "operational_domain":canvas.operational_domain.value, "distance_km":float(canvas.distance_km),
            "cloud_base_altitude_km":float(canvas.cloud_base_altitude_km),
            "target_optical_truth_state":truth, "target_cot_semantics":semantics,
            "target_response_eligibility":eligibility, "cot_readiness_state":cot_state,
            "cot_exact_or_bounded":bool(cot_ok),
            "cot_lower_bound":float(cot_lo) if _finite(cot_lo) else None,
            "cot_upper_bound":float(cot_hi) if _finite(cot_hi) else None,
            "phase":phase, "phase_readiness_state":"PHASE_READY" if phase_ok else "PHASE_MISSING",
            "effective_radius_um":float(reff) if reff_ok else None,
            "reff_readiness_state":"REFF_READY" if reff_ok else "REFF_MISSING",
            "cloud_thickness_km":float(thickness) if thickness_ok else None,
            "thickness_readiness_state":"THICKNESS_READY" if thickness_ok else "THICKNESS_MISSING",
            "six_band_incident_readiness_state":incident_state,
            "six_band_incident_ready_count":int(incident_count),
            "required_wavelength_count":int(len(SIX_BAND_WAVELENGTHS_NM)),
            "required_wavelengths_nm":"/".join(str(int(x)) for x in SIX_BAND_WAVELENGTHS_NM),
            "tier2_input_completeness_fraction":completeness,
            "tier2_input_contract_state":contract,
            "scattering_lut_state":lut_state, "scattering_solver_state":solver_state,
            "tier2_response_eligibility":response_eligibility, "blocking_reason":reason,
            "cf_or_rh_used_to_infer_cot":False, "tier2_contract_version":"R5.7.17_TIER2_READINESS_V1",
        })
    return pd.DataFrame(rows, columns=TIER2_SCATTERING_READINESS_COLUMNS)


def summarize_tier2_scattering_readiness(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=TIER2_SCATTERING_READINESS_SUMMARY_COLUMNS)
    rows=[]
    for angle,g in df.groupby("solar_altitude_deg", sort=False):
        s=g["tier2_input_contract_state"].astype(str)
        n=len(g)
        ready=int(s.eq("INPUTS_READY_AWAITING_LUT_SOLVER").sum())
        response_ready=int(g["tier2_response_eligibility"].astype(str).eq("READY_TIER2_RESPONSE").sum())
        if n == 0:
            closure="NOT_APPLICABLE"
        elif ready == n:
            closure="INPUTS_CLOSED_AWAITING_LUT_SOLVER"
        elif s.eq("BLOCKED_COT_CONFLICT").any():
            closure="COT_CONFLICT_UNRESOLVED"
        else:
            closure="TIER2_INPUTS_PARTIAL"
        rows.append({
            "solar_altitude_deg":float(angle), "canvas_count":int(n), "inputs_ready_count":ready,
            "blocked_cot_conflict_count":int(s.eq("BLOCKED_COT_CONFLICT").sum()),
            "blocked_cot_missing_count":int(s.eq("BLOCKED_COT_MISSING").sum()),
            "blocked_phase_count":int(s.eq("BLOCKED_PHASE_MISSING").sum()),
            "blocked_reff_count":int(s.eq("BLOCKED_REFF_MISSING").sum()),
            "blocked_thickness_count":int(s.eq("BLOCKED_THICKNESS_MISSING").sum()),
            "blocked_six_band_count":int(s.eq("BLOCKED_SIX_BAND_INCIDENT_INCOMPLETE").sum()),
            "awaiting_lut_solver_count":int(g["tier2_response_eligibility"].astype(str).eq("AWAITING_LUT_SOLVER").sum()),
            "response_ready_count":response_ready,
            "mean_input_completeness_fraction":float(pd.to_numeric(g["tier2_input_completeness_fraction"],errors="coerce").mean()),
            "closure_state":closure, "tier2_contract_version":"R5.7.17_TIER2_READINESS_V1",
        })
    return pd.DataFrame(rows, columns=TIER2_SCATTERING_READINESS_SUMMARY_COLUMNS)
