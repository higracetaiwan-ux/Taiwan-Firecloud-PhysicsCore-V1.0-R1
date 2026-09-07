from __future__ import annotations
"""R5.7.19 Tier-2 calibrated LUT interpolation-domain contract.

This module answers only whether a target can be interpolated safely from an
installed calibrated LUT. It does not calculate a scattering response.
"""

import itertools
import math
from typing import Any

import numpy as np
import pandas as pd

from .contracts import SIX_BAND_WAVELENGTHS_NM

DOMAIN_CONTRACT = "R5.7.19_TIER2_SCATTERING_INTERPOLATION_DOMAIN_V1"

TIER2_SCATTERING_DOMAIN_COLUMNS = [
    "time", "solar_altitude_deg", "canvas_id", "cloud_layer_id", "operational_domain", "distance_km",
    "target_optical_truth_state", "target_cot_semantics", "phase", "cot_lower_bound", "cot_upper_bound",
    "effective_radius_um", "cloud_thickness_km", "scattering_angle_deg",
    "lut_runtime_state", "lut_version", "calibration_id", "phase_domain_state",
    "cot_domain_state", "reff_domain_state", "thickness_domain_state", "scattering_angle_domain_state",
    "six_band_domain_ready_count", "required_wavelength_count", "local_cell_state",
    "interpolation_domain_state", "deterministic_interpolation_eligible", "bounded_interpolation_eligible",
    "blocking_reason", "interpolation_executed", "domain_contract_version",
]

TIER2_SCATTERING_DOMAIN_SUMMARY_COLUMNS = [
    "solar_altitude_deg", "canvas_count", "domain_ready_deterministic_count", "domain_ready_bounded_count",
    "blocked_input_count", "lut_unavailable_count", "phase_unsupported_count", "cot_out_of_domain_count",
    "reff_out_of_domain_count", "thickness_out_of_domain_count", "scattering_angle_out_of_domain_count",
    "local_cell_incomplete_count", "closure_state", "domain_contract_version",
]


def _finite(v: Any) -> bool:
    try:
        return bool(math.isfinite(float(v)))
    except Exception:
        return False


def _phase(v: Any) -> str:
    p = str(v or "").strip().upper()
    return "LIQUID" if p == "WATER" else p


def _bracket(values: pd.Series, x: float) -> tuple[float, float] | None:
    vals = sorted(set(float(v) for v in pd.to_numeric(values, errors="coerce").dropna().tolist()))
    if not vals or x < vals[0] or x > vals[-1]:
        return None
    lo = max(v for v in vals if v <= x)
    hi = min(v for v in vals if v >= x)
    return lo, hi


def _axis_state(values: pd.Series, x: float, label: str) -> tuple[str, tuple[float, float] | None]:
    b = _bracket(values, x)
    return ((label + "_DOMAIN_READY", b) if b is not None else (label + "_OUT_OF_DOMAIN", None))




def _cot_interval_probes(values: pd.Series, lo: float, hi: float) -> list[float]:
    """Return conservative probes covering every LUT cell crossed by [lo, hi]."""
    if lo > hi:
        lo, hi = hi, lo
    vals = sorted(set(float(v) for v in pd.to_numeric(values, errors="coerce").dropna().tolist()))
    if not vals or lo < vals[0] or hi > vals[-1]:
        return []
    knots = [v for v in vals if lo <= v <= hi]
    points = {float(lo), float(hi), *[float(v) for v in knots]}
    edges = [float(lo)] + [float(v) for v in knots if lo < v < hi] + [float(hi)]
    edges = sorted(set(edges))
    for a, b in zip(edges, edges[1:]):
        if b > a:
            points.add((a + b) / 2.0)
    return sorted(points)

def _cell_complete(q: pd.DataFrame, *, phase: str, wl: int, cot: float, reff: float, thickness: float, angle: float) -> tuple[bool, str]:
    p = q[(q["phase"] == phase) & (q["wavelength_nm"].astype(int) == int(wl))]
    if p.empty:
        return False, "WAVELENGTH_PHASE_GRID_MISSING"
    brackets = []
    for col, x in [("cot", cot), ("effective_radius_um", reff), ("cloud_thickness_km", thickness), ("scattering_angle_deg", angle)]:
        b = _bracket(p[col], x)
        if b is None:
            return False, "LOCAL_AXIS_OUT_OF_DOMAIN:" + col
        brackets.append(sorted(set(b)))
    needed = list(itertools.product(*brackets))
    coords = set(
        (float(r.cot), float(r.effective_radius_um), float(r.cloud_thickness_km), float(r.scattering_angle_deg))
        for r in p.itertuples(index=False)
    )
    missing = [c for c in needed if tuple(float(x) for x in c) not in coords]
    if missing:
        return False, f"LOCAL_CELL_MISSING_CORNERS:{len(missing)}/{len(needed)}"
    return True, "LOCAL_CELL_COMPLETE"


def evaluate_tier2_scattering_domain(
    *, foundation: pd.DataFrame, readiness: pd.DataFrame,
    calibrated_lut: pd.DataFrame | None, lut_audit: dict[str, Any] | None = None,
) -> pd.DataFrame:
    if foundation is None or foundation.empty:
        return pd.DataFrame(columns=TIER2_SCATTERING_DOMAIN_COLUMNS)
    lut_audit = dict(lut_audit or {})
    lut_ok = bool(lut_audit.get("ok")) and calibrated_lut is not None and not calibrated_lut.empty
    q = calibrated_lut.copy() if lut_ok else pd.DataFrame()
    if lut_ok:
        q["phase"] = q["phase"].map(_phase)
    rmap = {str(r.get("canvas_id")): r for _, r in readiness.iterrows()} if readiness is not None and not readiness.empty else {}
    rows = []
    for _, f in foundation.iterrows():
        cid = str(f.get("canvas_id"))
        r = rmap.get(cid)
        input_state = str(f.get("tier2_input_contract_state", "BLOCKED_INPUT_CONTRACT_MISSING"))
        geom_state = str(f.get("scattering_geometry_state", "SCATTERING_GEOMETRY_MISSING"))
        truth = str(r.get("target_optical_truth_state", "")) if r is not None else ""
        semantics = str(r.get("target_cot_semantics", "")) if r is not None else ""
        phase = _phase(r.get("phase")) if r is not None else ""
        cot_lo = float(r.get("cot_lower_bound")) if r is not None and _finite(r.get("cot_lower_bound")) else np.nan
        cot_hi = float(r.get("cot_upper_bound")) if r is not None and _finite(r.get("cot_upper_bound")) else np.nan
        reff = float(r.get("effective_radius_um")) if r is not None and _finite(r.get("effective_radius_um")) else np.nan
        thick = float(r.get("cloud_thickness_km")) if r is not None and _finite(r.get("cloud_thickness_km")) else np.nan
        angle = float(f.get("scattering_angle_deg")) if _finite(f.get("scattering_angle_deg")) else np.nan
        phase_state = cot_state = reff_state = thick_state = angle_state = "NOT_EVALUATED"
        six_ready = 0
        local_state = "NOT_EVALUATED"
        deterministic = bounded = False

        if input_state != "INPUTS_READY_AWAITING_LUT_SOLVER":
            state = "BLOCKED_INPUT_CONTRACT"; reason = input_state
        elif geom_state != "SCATTERING_GEOMETRY_READY" or not _finite(angle):
            state = "BLOCKED_SCATTERING_GEOMETRY"; reason = "SCATTERING_ANGLE_MISSING"
        elif not lut_ok:
            state = "LUT_NOT_AVAILABLE_OR_INVALID"; reason = str(lut_audit.get("state", "CALIBRATED_LUT_NOT_INSTALLED"))
        else:
            p = q[q["phase"] == phase]
            if p.empty:
                state = "LUT_PHASE_UNSUPPORTED"; reason = "PHASE_NOT_IN_CALIBRATED_LUT"; phase_state = "PHASE_UNSUPPORTED"
            else:
                phase_state = "PHASE_DOMAIN_READY"
                # Exact values have equal bounds. Bounded values must fit at both endpoints.
                cot_probe = [cot_lo, cot_hi] if _finite(cot_lo) and _finite(cot_hi) else []
                cot_ok = bool(cot_probe) and all(_bracket(p["cot"], x) is not None for x in cot_probe)
                cot_state = "COT_DOMAIN_READY" if cot_ok else "COT_OUT_OF_DOMAIN"
                reff_state, _ = _axis_state(p["effective_radius_um"], reff, "REFF")
                thick_state, _ = _axis_state(p["cloud_thickness_km"], thick, "THICKNESS")
                angle_state, _ = _axis_state(p["scattering_angle_deg"], angle, "SCATTERING_ANGLE")
                if not cot_ok:
                    state = "LUT_COT_OUT_OF_DOMAIN"; reason = cot_state
                elif reff_state != "REFF_DOMAIN_READY":
                    state = "LUT_REFF_OUT_OF_DOMAIN"; reason = reff_state
                elif thick_state != "THICKNESS_DOMAIN_READY":
                    state = "LUT_THICKNESS_OUT_OF_DOMAIN"; reason = thick_state
                elif angle_state != "SCATTERING_ANGLE_DOMAIN_READY":
                    state = "LUT_SCATTERING_ANGLE_OUT_OF_DOMAIN"; reason = angle_state
                else:
                    missing_detail = ""
                    for wl in SIX_BAND_WAVELENGTHS_NM:
                        wl_ok = True
                        detail = ""
                        pw = p[p["wavelength_nm"].astype(int) == int(wl)]
                        probes = (
                            _cot_interval_probes(pw["cot"], float(cot_lo), float(cot_hi))
                            if truth == "BOUNDED_NATIVE_BRACKET" and semantics == "BOUNDED_INTERVAL"
                            else sorted(set(cot_probe))
                        )
                        if not probes:
                            wl_ok = False
                            detail = "COT_INTERVAL_NOT_FULLY_COVERED"
                        for cot in probes:
                            ok, detail = _cell_complete(p, phase=phase, wl=int(wl), cot=float(cot), reff=reff, thickness=thick, angle=angle)
                            if not ok:
                                wl_ok = False
                                break
                        if wl_ok:
                            six_ready += 1
                        elif not missing_detail:
                            missing_detail = f"{int(wl)}nm:{detail}"
                    if six_ready != len(SIX_BAND_WAVELENGTHS_NM):
                        state = "LUT_LOCAL_CELL_INCOMPLETE"; reason = missing_detail or "LOCAL_CELL_INCOMPLETE"; local_state = "LOCAL_CELL_INCOMPLETE"
                    elif truth.startswith("EXACT_") and semantics == "EXACT_VALUE":
                        state = "INTERPOLATION_DOMAIN_READY_DETERMINISTIC"; reason = "NONE_DOMAIN_COMPLETE"; local_state = "LOCAL_CELL_COMPLETE_ALL_SIX_BANDS"; deterministic = True
                    elif truth == "BOUNDED_NATIVE_BRACKET" and semantics == "BOUNDED_INTERVAL":
                        state = "INTERPOLATION_DOMAIN_READY_BOUNDED"; reason = "NONE_DOMAIN_COMPLETE_BOUNDS"; local_state = "LOCAL_CELL_COMPLETE_ALL_SIX_BANDS_AT_BOUNDS"; bounded = True
                    else:
                        state = "BLOCKED_OPTICAL_TRUTH_SEMANTICS"; reason = truth + ":" + semantics; local_state = "LOCAL_CELL_COMPLETE_BUT_TRUTH_NOT_ELIGIBLE"
        rows.append({
            "time": f.get("time"), "solar_altitude_deg": f.get("solar_altitude_deg"), "canvas_id": f.get("canvas_id"),
            "cloud_layer_id": f.get("cloud_layer_id"), "operational_domain": f.get("operational_domain"), "distance_km": f.get("distance_km"),
            "target_optical_truth_state": truth, "target_cot_semantics": semantics, "phase": phase,
            "cot_lower_bound": cot_lo if _finite(cot_lo) else None, "cot_upper_bound": cot_hi if _finite(cot_hi) else None,
            "effective_radius_um": reff if _finite(reff) else None, "cloud_thickness_km": thick if _finite(thick) else None,
            "scattering_angle_deg": angle if _finite(angle) else None,
            "lut_runtime_state": str(lut_audit.get("state", "CALIBRATED_LUT_NOT_INSTALLED")),
            "lut_version": str(lut_audit.get("lut_version", "")), "calibration_id": str(lut_audit.get("calibration_id", "")),
            "phase_domain_state": phase_state, "cot_domain_state": cot_state, "reff_domain_state": reff_state,
            "thickness_domain_state": thick_state, "scattering_angle_domain_state": angle_state,
            "six_band_domain_ready_count": int(six_ready), "required_wavelength_count": int(len(SIX_BAND_WAVELENGTHS_NM)),
            "local_cell_state": local_state, "interpolation_domain_state": state,
            "deterministic_interpolation_eligible": bool(deterministic), "bounded_interpolation_eligible": bool(bounded),
            "blocking_reason": reason, "interpolation_executed": False, "domain_contract_version": DOMAIN_CONTRACT,
        })
    return pd.DataFrame(rows, columns=TIER2_SCATTERING_DOMAIN_COLUMNS)


def summarize_tier2_scattering_domain(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=TIER2_SCATTERING_DOMAIN_SUMMARY_COLUMNS)
    rows = []
    for a, g in df.groupby("solar_altitude_deg", sort=False):
        s = g["interpolation_domain_state"].astype(str)
        det = int(s.eq("INTERPOLATION_DOMAIN_READY_DETERMINISTIC").sum())
        bnd = int(s.eq("INTERPOLATION_DOMAIN_READY_BOUNDED").sum())
        if det or bnd:
            closure = "INTERPOLATION_DOMAIN_READY"
        elif s.eq("LUT_NOT_AVAILABLE_OR_INVALID").any():
            closure = "CALIBRATED_LUT_UNAVAILABLE"
        else:
            closure = "TARGET_OR_DOMAIN_BLOCKED"
        rows.append({
            "solar_altitude_deg": float(a), "canvas_count": int(len(g)),
            "domain_ready_deterministic_count": det, "domain_ready_bounded_count": bnd,
            "blocked_input_count": int(s.eq("BLOCKED_INPUT_CONTRACT").sum()),
            "lut_unavailable_count": int(s.eq("LUT_NOT_AVAILABLE_OR_INVALID").sum()),
            "phase_unsupported_count": int(s.eq("LUT_PHASE_UNSUPPORTED").sum()),
            "cot_out_of_domain_count": int(s.eq("LUT_COT_OUT_OF_DOMAIN").sum()),
            "reff_out_of_domain_count": int(s.eq("LUT_REFF_OUT_OF_DOMAIN").sum()),
            "thickness_out_of_domain_count": int(s.eq("LUT_THICKNESS_OUT_OF_DOMAIN").sum()),
            "scattering_angle_out_of_domain_count": int(s.eq("LUT_SCATTERING_ANGLE_OUT_OF_DOMAIN").sum()),
            "local_cell_incomplete_count": int(s.eq("LUT_LOCAL_CELL_INCOMPLETE").sum()),
            "closure_state": closure, "domain_contract_version": DOMAIN_CONTRACT,
        })
    return pd.DataFrame(rows, columns=TIER2_SCATTERING_DOMAIN_SUMMARY_COLUMNS)


def scattering_lut_audit_frame(audit: dict[str, Any] | None) -> pd.DataFrame:
    audit = dict(audit or {})
    row = {
        "state": audit.get("state", "CALIBRATED_LUT_NOT_INSTALLED"),
        "ok": bool(audit.get("ok", False)),
        "source": audit.get("source", ""),
        "csv_path": audit.get("csv_path", ""),
        "manifest_path": audit.get("manifest_path", ""),
        "lut_version": audit.get("lut_version", ""),
        "calibration_id": audit.get("calibration_id", ""),
        "calibration_source": audit.get("calibration_source", ""),
        "calibration_date": audit.get("calibration_date", ""),
        "supported_phases": audit.get("supported_phases", ""),
        "solver_eligible": bool(audit.get("solver_eligible", False)),
        "production_calibration_state": audit.get("production_calibration_state", ""),
        "calibration_contract": audit.get("calibration_contract", ""),
        "qc_state": audit.get("qc_state", ""),
        "solver_family": audit.get("solver_family", ""),
        "solver_version": audit.get("solver_version", ""),
        "cloud_optics_source": audit.get("cloud_optics_source", ""),
        "phase_function_source": audit.get("phase_function_source", ""),
        "multiple_scattering_enabled": bool(audit.get("multiple_scattering_enabled", False)),
        "response_definition": audit.get("response_definition", ""),
        "response_units": audit.get("response_units", ""),
        "geometry_convention": audit.get("geometry_convention", ""),
        "validation_reference": audit.get("validation_reference", ""),
        "rows": int(audit.get("rows", 0) or 0),
        "csv_sha256": audit.get("csv_sha256", ""),
        "errors": ";".join(str(x) for x in audit.get("errors", []) or []),
        "warnings": ";".join(str(x) for x in audit.get("warnings", []) or []),
        "runtime_contract": audit.get("runtime_contract", "R5.7.19_TIER2_SCATTERING_LUT_RUNTIME_V1"),
    }
    return pd.DataFrame([row])
