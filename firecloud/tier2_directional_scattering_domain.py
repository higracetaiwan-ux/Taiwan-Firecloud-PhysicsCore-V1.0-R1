from __future__ import annotations
"""R5.7.22 full-directional Tier-2 LUT interpolation-domain contract."""

import itertools
import math
from typing import Any

import numpy as np
import pandas as pd

from .contracts import SIX_BAND_WAVELENGTHS_NM
from .tier2_directional_scattering_calibration import DIRECTIONAL_INTERPOLATION_AXES

DOMAIN_CONTRACT = "R5.7.22_TIER2_DIRECTIONAL_SCATTERING_INTERPOLATION_DOMAIN_V2"

TIER2_DIRECTIONAL_SCATTERING_DOMAIN_COLUMNS = [
    "time", "solar_altitude_deg", "canvas_id", "cloud_layer_id", "operational_domain", "distance_km",
    "target_optical_truth_state", "target_cot_semantics", "phase", "cot_lower_bound", "cot_upper_bound",
    "effective_radius_um", "cloud_thickness_km",
    "solar_zenith_deg", "view_zenith_deg", "relative_azimuth_deg", "scattering_angle_deg",
    "solar_altitude_target_deg", "solar_azimuth_target_deg", "view_elevation_deg", "view_azimuth_target_deg",
    "mu0", "mu_view", "azimuth_degeneracy_state", "directional_geometry_state",
    "lut_runtime_state", "lut_version", "calibration_id", "phase_domain_state",
    "cot_domain_state", "reff_domain_state", "solar_zenith_domain_state", "view_zenith_domain_state",
    "relative_azimuth_domain_state", "six_band_domain_ready_count", "required_wavelength_count",
    "local_cell_state", "interpolation_domain_state", "deterministic_interpolation_eligible",
    "bounded_interpolation_eligible", "blocking_reason", "interpolation_executed", "domain_contract_version",
]

TIER2_DIRECTIONAL_SCATTERING_DOMAIN_SUMMARY_COLUMNS = [
    "solar_altitude_deg", "canvas_count", "domain_ready_deterministic_count", "domain_ready_bounded_count",
    "blocked_input_count", "blocked_geometry_count", "lut_unavailable_count", "phase_unsupported_count",
    "cot_out_of_domain_count", "reff_out_of_domain_count", "solar_zenith_out_of_domain_count",
    "view_zenith_out_of_domain_count", "relative_azimuth_out_of_domain_count", "local_cell_incomplete_count",
    "closure_state", "domain_contract_version",
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
    return max(v for v in vals if v <= x), min(v for v in vals if v >= x)


def _axis_state(values: pd.Series, x: float, label: str) -> tuple[str, tuple[float, float] | None]:
    b = _bracket(values, x)
    return ((label + "_DOMAIN_READY", b) if b is not None else (label + "_OUT_OF_DOMAIN", None))


def _cot_interval_probes(values: pd.Series, lo: float, hi: float) -> list[float]:
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


def _cell_complete(
    q: pd.DataFrame,
    *, phase: str, wl: int, cot: float, reff: float,
    solar_zenith: float, view_zenith: float, relative_azimuth: float,
) -> tuple[bool, str]:
    p = q[(q["phase"] == phase) & (q["wavelength_nm"].astype(int) == int(wl))]
    if p.empty:
        return False, "WAVELENGTH_PHASE_GRID_MISSING"
    probes = [
        ("cot", cot),
        ("effective_radius_um", reff),
        ("solar_zenith_deg", solar_zenith),
        ("view_zenith_deg", view_zenith),
        ("relative_azimuth_deg", relative_azimuth),
    ]
    brackets = []
    for col, x in probes:
        b = _bracket(p[col], x)
        if b is None:
            return False, "LOCAL_AXIS_OUT_OF_DOMAIN:" + col
        brackets.append(sorted(set(b)))
    needed = list(itertools.product(*brackets))
    coords = set(
        (
            float(r.cot), float(r.effective_radius_um), float(r.solar_zenith_deg),
            float(r.view_zenith_deg), float(r.relative_azimuth_deg),
        )
        for r in p.itertuples(index=False)
    )
    missing = [c for c in needed if tuple(float(x) for x in c) not in coords]
    if missing:
        return False, f"LOCAL_DIRECTIONAL_CELL_MISSING_CORNERS:{len(missing)}/{len(needed)}"
    return True, "LOCAL_DIRECTIONAL_CELL_COMPLETE"


def evaluate_tier2_directional_scattering_domain(
    *, foundation: pd.DataFrame, readiness: pd.DataFrame,
    calibrated_lut: pd.DataFrame | None, lut_audit: dict[str, Any] | None = None,
) -> pd.DataFrame:
    if foundation is None or foundation.empty:
        return pd.DataFrame(columns=TIER2_DIRECTIONAL_SCATTERING_DOMAIN_COLUMNS)
    audit = dict(lut_audit or {})
    lut_ok = bool(audit.get("ok")) and calibrated_lut is not None and not calibrated_lut.empty
    q = calibrated_lut.copy() if lut_ok else pd.DataFrame()
    if lut_ok:
        q["phase"] = q["phase"].map(_phase)
    rmap = {str(r.get("canvas_id")): r for _, r in readiness.iterrows()} if readiness is not None and not readiness.empty else {}
    rows = []
    for _, f in foundation.iterrows():
        cid = str(f.get("canvas_id"))
        r = rmap.get(cid)
        input_state = str(f.get("tier2_input_contract_state", "BLOCKED_INPUT_CONTRACT_MISSING"))
        directional_state = str(f.get("directional_geometry_state", "FULL_DIRECTIONAL_GEOMETRY_MISSING"))
        truth = str(r.get("target_optical_truth_state", "")) if r is not None else ""
        semantics = str(r.get("target_cot_semantics", "")) if r is not None else ""
        phase = _phase(r.get("phase")) if r is not None else ""
        cot_lo = float(r.get("cot_lower_bound")) if r is not None and _finite(r.get("cot_lower_bound")) else np.nan
        cot_hi = float(r.get("cot_upper_bound")) if r is not None and _finite(r.get("cot_upper_bound")) else np.nan
        reff = float(r.get("effective_radius_um")) if r is not None and _finite(r.get("effective_radius_um")) else np.nan
        thick = float(r.get("cloud_thickness_km")) if r is not None and _finite(r.get("cloud_thickness_km")) else np.nan
        theta0 = float(f.get("solar_zenith_deg")) if _finite(f.get("solar_zenith_deg")) else np.nan
        thetav = float(f.get("view_zenith_deg")) if _finite(f.get("view_zenith_deg")) else np.nan
        relaz = float(f.get("relative_azimuth_deg")) if _finite(f.get("relative_azimuth_deg")) else np.nan
        scat = float(f.get("scattering_angle_deg")) if _finite(f.get("scattering_angle_deg")) else np.nan

        phase_state = cot_state = reff_state = theta0_state = thetav_state = relaz_state = "NOT_EVALUATED"
        six_ready = 0
        local_state = "NOT_EVALUATED"
        deterministic = bounded = False

        if input_state != "INPUTS_READY_AWAITING_LUT_SOLVER":
            state = "BLOCKED_INPUT_CONTRACT"; reason = input_state
        elif directional_state != "FULL_DIRECTIONAL_GEOMETRY_READY" or not all(_finite(v) for v in (theta0, thetav, relaz, scat)):
            state = "BLOCKED_DIRECTIONAL_GEOMETRY"; reason = "THETA0_THETAV_DELTAPHI_OR_SCATTERING_DIAGNOSTIC_MISSING"
        elif not lut_ok:
            state = "LUT_NOT_AVAILABLE_OR_INVALID"; reason = str(audit.get("state", "CALIBRATED_DIRECTIONAL_LUT_NOT_INSTALLED"))
        else:
            p = q[q["phase"] == phase]
            if p.empty:
                state = "LUT_PHASE_UNSUPPORTED"; reason = "PHASE_NOT_IN_DIRECTIONAL_LUT"; phase_state = "PHASE_UNSUPPORTED"
            else:
                phase_state = "PHASE_DOMAIN_READY"
                cot_probe = [cot_lo, cot_hi] if _finite(cot_lo) and _finite(cot_hi) else []
                cot_ok = bool(cot_probe) and all(_bracket(p["cot"], x) is not None for x in cot_probe)
                cot_state = "COT_DOMAIN_READY" if cot_ok else "COT_OUT_OF_DOMAIN"
                reff_state, _ = _axis_state(p["effective_radius_um"], reff, "REFF")
                theta0_state, _ = _axis_state(p["solar_zenith_deg"], theta0, "SOLAR_ZENITH")
                thetav_state, _ = _axis_state(p["view_zenith_deg"], thetav, "VIEW_ZENITH")
                relaz_state, _ = _axis_state(p["relative_azimuth_deg"], relaz, "RELATIVE_AZIMUTH")
                if not cot_ok:
                    state = "LUT_COT_OUT_OF_DOMAIN"; reason = cot_state
                elif reff_state != "REFF_DOMAIN_READY":
                    state = "LUT_REFF_OUT_OF_DOMAIN"; reason = reff_state
                elif theta0_state != "SOLAR_ZENITH_DOMAIN_READY":
                    state = "LUT_SOLAR_ZENITH_OUT_OF_DOMAIN"; reason = theta0_state
                elif thetav_state != "VIEW_ZENITH_DOMAIN_READY":
                    state = "LUT_VIEW_ZENITH_OUT_OF_DOMAIN"; reason = thetav_state
                elif relaz_state != "RELATIVE_AZIMUTH_DOMAIN_READY":
                    state = "LUT_RELATIVE_AZIMUTH_OUT_OF_DOMAIN"; reason = relaz_state
                else:
                    missing_detail = ""
                    for wl in SIX_BAND_WAVELENGTHS_NM:
                        pw = p[p["wavelength_nm"].astype(int) == int(wl)]
                        probes = (
                            _cot_interval_probes(pw["cot"], float(cot_lo), float(cot_hi))
                            if truth == "BOUNDED_NATIVE_BRACKET" and semantics == "BOUNDED_INTERVAL"
                            else sorted(set(cot_probe))
                        )
                        wl_ok = bool(probes)
                        detail = "COT_INTERVAL_NOT_FULLY_COVERED" if not probes else ""
                        for cot in probes:
                            ok, detail = _cell_complete(
                                p, phase=phase, wl=int(wl), cot=float(cot), reff=reff,
                                solar_zenith=theta0, view_zenith=thetav, relative_azimuth=relaz,
                            )
                            if not ok:
                                wl_ok = False
                                break
                        if wl_ok:
                            six_ready += 1
                        elif not missing_detail:
                            missing_detail = f"{int(wl)}nm:{detail}"
                    if six_ready != len(SIX_BAND_WAVELENGTHS_NM):
                        state = "LUT_LOCAL_CELL_INCOMPLETE"; reason = missing_detail or "LOCAL_DIRECTIONAL_CELL_INCOMPLETE"; local_state = "LOCAL_DIRECTIONAL_CELL_INCOMPLETE"
                    elif truth.startswith("EXACT_") and semantics == "EXACT_VALUE":
                        state = "INTERPOLATION_DOMAIN_READY_DETERMINISTIC"; reason = "NONE_DIRECTIONAL_DOMAIN_COMPLETE"; local_state = "LOCAL_DIRECTIONAL_CELL_COMPLETE_ALL_SIX_BANDS"; deterministic = True
                    elif truth == "BOUNDED_NATIVE_BRACKET" and semantics == "BOUNDED_INTERVAL":
                        state = "INTERPOLATION_DOMAIN_READY_BOUNDED"; reason = "NONE_DIRECTIONAL_DOMAIN_COMPLETE_BOUNDS"; local_state = "LOCAL_DIRECTIONAL_CELL_COMPLETE_ALL_SIX_BANDS_AT_BOUNDS"; bounded = True
                    else:
                        state = "BLOCKED_OPTICAL_TRUTH_SEMANTICS"; reason = truth + ":" + semantics; local_state = "LOCAL_DIRECTIONAL_CELL_COMPLETE_BUT_TRUTH_NOT_ELIGIBLE"

        rows.append({
            "time": f.get("time"), "solar_altitude_deg": f.get("solar_altitude_deg"), "canvas_id": f.get("canvas_id"),
            "cloud_layer_id": f.get("cloud_layer_id"), "operational_domain": f.get("operational_domain"), "distance_km": f.get("distance_km"),
            "target_optical_truth_state": truth, "target_cot_semantics": semantics, "phase": phase,
            "cot_lower_bound": cot_lo if _finite(cot_lo) else None, "cot_upper_bound": cot_hi if _finite(cot_hi) else None,
            "effective_radius_um": reff if _finite(reff) else None, "cloud_thickness_km": thick if _finite(thick) else None,
            "solar_zenith_deg": theta0 if _finite(theta0) else None, "view_zenith_deg": thetav if _finite(thetav) else None,
            "relative_azimuth_deg": relaz if _finite(relaz) else None, "scattering_angle_deg": scat if _finite(scat) else None,
            "solar_altitude_target_deg": f.get("solar_altitude_target_deg"), "solar_azimuth_target_deg": f.get("solar_azimuth_target_deg"),
            "view_elevation_deg": f.get("view_elevation_deg"), "view_azimuth_target_deg": f.get("view_azimuth_target_deg"),
            "mu0": f.get("mu0"), "mu_view": f.get("mu_view"), "azimuth_degeneracy_state": f.get("azimuth_degeneracy_state"),
            "directional_geometry_state": directional_state,
            "lut_runtime_state": str(audit.get("state", "CALIBRATED_DIRECTIONAL_LUT_NOT_INSTALLED")),
            "lut_version": str(audit.get("lut_version", "")), "calibration_id": str(audit.get("calibration_id", "")),
            "phase_domain_state": phase_state, "cot_domain_state": cot_state, "reff_domain_state": reff_state,
            "solar_zenith_domain_state": theta0_state, "view_zenith_domain_state": thetav_state,
            "relative_azimuth_domain_state": relaz_state, "six_band_domain_ready_count": int(six_ready),
            "required_wavelength_count": int(len(SIX_BAND_WAVELENGTHS_NM)), "local_cell_state": local_state,
            "interpolation_domain_state": state, "deterministic_interpolation_eligible": bool(deterministic),
            "bounded_interpolation_eligible": bool(bounded), "blocking_reason": reason,
            "interpolation_executed": False, "domain_contract_version": DOMAIN_CONTRACT,
        })
    return pd.DataFrame(rows, columns=TIER2_DIRECTIONAL_SCATTERING_DOMAIN_COLUMNS)


def summarize_tier2_directional_scattering_domain(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=TIER2_DIRECTIONAL_SCATTERING_DOMAIN_SUMMARY_COLUMNS)
    rows = []
    for a, g in df.groupby("solar_altitude_deg", sort=False):
        s = g["interpolation_domain_state"].astype(str)
        det = int(s.eq("INTERPOLATION_DOMAIN_READY_DETERMINISTIC").sum())
        bnd = int(s.eq("INTERPOLATION_DOMAIN_READY_BOUNDED").sum())
        if det or bnd:
            closure = "INTERPOLATION_DOMAIN_READY"
        elif s.eq("LUT_NOT_AVAILABLE_OR_INVALID").any():
            closure = "CALIBRATED_DIRECTIONAL_LUT_UNAVAILABLE"
        else:
            closure = "TARGET_OR_DIRECTIONAL_DOMAIN_BLOCKED"
        rows.append({
            "solar_altitude_deg": float(a), "canvas_count": int(len(g)),
            "domain_ready_deterministic_count": det, "domain_ready_bounded_count": bnd,
            "blocked_input_count": int(s.eq("BLOCKED_INPUT_CONTRACT").sum()),
            "blocked_geometry_count": int(s.eq("BLOCKED_DIRECTIONAL_GEOMETRY").sum()),
            "lut_unavailable_count": int(s.eq("LUT_NOT_AVAILABLE_OR_INVALID").sum()),
            "phase_unsupported_count": int(s.eq("LUT_PHASE_UNSUPPORTED").sum()),
            "cot_out_of_domain_count": int(s.eq("LUT_COT_OUT_OF_DOMAIN").sum()),
            "reff_out_of_domain_count": int(s.eq("LUT_REFF_OUT_OF_DOMAIN").sum()),
            "solar_zenith_out_of_domain_count": int(s.eq("LUT_SOLAR_ZENITH_OUT_OF_DOMAIN").sum()),
            "view_zenith_out_of_domain_count": int(s.eq("LUT_VIEW_ZENITH_OUT_OF_DOMAIN").sum()),
            "relative_azimuth_out_of_domain_count": int(s.eq("LUT_RELATIVE_AZIMUTH_OUT_OF_DOMAIN").sum()),
            "local_cell_incomplete_count": int(s.eq("LUT_LOCAL_CELL_INCOMPLETE").sum()),
            "closure_state": closure, "domain_contract_version": DOMAIN_CONTRACT,
        })
    return pd.DataFrame(rows, columns=TIER2_DIRECTIONAL_SCATTERING_DOMAIN_SUMMARY_COLUMNS)


def directional_scattering_lut_audit_frame(audit: dict[str, Any] | None) -> pd.DataFrame:
    audit = dict(audit or {})
    row = {
        "state": audit.get("state", "CALIBRATED_DIRECTIONAL_LUT_NOT_INSTALLED"),
        "ok": bool(audit.get("ok", False)), "source": audit.get("source", ""),
        "csv_path": audit.get("csv_path", ""), "manifest_path": audit.get("manifest_path", ""),
        "lut_version": audit.get("lut_version", ""), "calibration_id": audit.get("calibration_id", ""),
        "calibration_source": audit.get("calibration_source", ""), "calibration_date": audit.get("calibration_date", ""),
        "supported_phases": audit.get("supported_phases", ""), "solver_eligible": bool(audit.get("solver_eligible", False)),
        "production_calibration_state": audit.get("production_calibration_state", ""),
        "calibration_contract": audit.get("calibration_contract", ""), "qc_state": audit.get("qc_state", ""),
        "solver_family": audit.get("solver_family", ""), "solver_version": audit.get("solver_version", ""),
        "cloud_optics_source": audit.get("cloud_optics_source", ""), "phase_function_source": audit.get("phase_function_source", ""),
        "multiple_scattering_enabled": bool(audit.get("multiple_scattering_enabled", False)),
        "response_definition": audit.get("response_definition", ""), "response_units": audit.get("response_units", ""),
        "geometry_convention": audit.get("geometry_convention", ""), "directional_hemisphere_support": audit.get("directional_hemisphere_support", ""),
        "interpolation_axes": audit.get("interpolation_axes", "/".join(DIRECTIONAL_INTERPOLATION_AXES)),
        "scattering_angle_role": audit.get("scattering_angle_role", "DERIVED_DIAGNOSTIC_NOT_INTERPOLATION_AXIS"),
        "cloud_thickness_role": audit.get("cloud_thickness_role", "TARGET_GEOMETRY_EVIDENCE_NOT_LUT_INTERPOLATION_AXIS"),
        "validation_reference": audit.get("validation_reference", ""), "rows": int(audit.get("rows", 0) or 0),
        "csv_sha256": audit.get("csv_sha256", ""),
        "errors": ";".join(str(x) for x in audit.get("errors", []) or []),
        "warnings": ";".join(str(x) for x in audit.get("warnings", []) or []),
        "runtime_contract": audit.get("runtime_contract", "R5.7.22_TIER2_DIRECTIONAL_SCATTERING_LUT_RUNTIME_V2"),
    }
    return pd.DataFrame([row])
