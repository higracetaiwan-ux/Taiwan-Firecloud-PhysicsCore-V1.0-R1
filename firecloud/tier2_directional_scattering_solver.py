from __future__ import annotations
"""R5.7.22 production full-directional Tier-2 cloud-scattering solver."""

import itertools
import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from .contracts import SIX_BAND_WAVELENGTHS_NM
from .tier2_directional_scattering_calibration import DIRECTIONAL_INTERPOLATION_AXES

SOLVER_CONTRACT = "R5.7.22_TIER2_DIRECTIONAL_SCATTERING_INTERPOLATION_SOLVER_V2"
_PHOTOPIC_V = {550: 0.995, 575: 0.952, 600: 0.631, 650: 0.107, 700: 0.0041, 750: 0.00012}

TIER2_DIRECTIONAL_SCATTERING_RESPONSE_COLUMNS = [
    "time", "solar_altitude_deg", "canvas_id", "cloud_layer_id", "operational_domain", "distance_km",
    "target_optical_truth_state", "target_cot_semantics", "phase", "cot_lower_bound", "cot_upper_bound",
    "effective_radius_um", "cloud_thickness_km", "solar_zenith_deg", "view_zenith_deg", "relative_azimuth_deg",
    "scattering_angle_deg", "solar_altitude_target_deg", "solar_azimuth_target_deg", "view_elevation_deg",
    "view_azimuth_target_deg", "mu0", "mu_view", "azimuth_degeneracy_state",
    "lut_runtime_state", "lut_version", "calibration_id", "calibration_contract", "solver_family", "solver_version",
    "response_definition", "response_units", "interpolation_domain_state", "interpolation_mode",
    "solver_execution_state", "response_state", "blocking_reason", "interpolation_executed",
    "brightness", "brightness_lower_bound", "brightness_upper_bound", "redness", "redness_lower_bound", "redness_upper_bound",
    *[f"incident_irradiance_{int(w)}nm" for w in SIX_BAND_WAVELENGTHS_NM],
    *[f"response_factor_{int(w)}nm" for w in SIX_BAND_WAVELENGTHS_NM],
    *[f"response_factor_{int(w)}nm_lower_bound" for w in SIX_BAND_WAVELENGTHS_NM],
    *[f"response_factor_{int(w)}nm_upper_bound" for w in SIX_BAND_WAVELENGTHS_NM],
    *[f"tier2_radiance_{int(w)}nm" for w in SIX_BAND_WAVELENGTHS_NM],
    *[f"tier2_radiance_{int(w)}nm_lower_bound" for w in SIX_BAND_WAVELENGTHS_NM],
    *[f"tier2_radiance_{int(w)}nm_upper_bound" for w in SIX_BAND_WAVELENGTHS_NM],
    "cf_or_rh_used_to_infer_cot", "solver_contract_version",
]

TIER2_DIRECTIONAL_SCATTERING_RESPONSE_SUMMARY_COLUMNS = [
    "solar_altitude_deg", "canvas_count", "deterministic_response_count", "bounded_response_count",
    "domain_blocked_count", "production_calibration_blocked_count", "incident_missing_count",
    "solver_error_count", "interpolation_executed_count", "closure_state", "solver_contract_version",
]


def _finite(v: Any) -> bool:
    try:
        return bool(math.isfinite(float(v)))
    except Exception:
        return False


def _phase(v: Any) -> str:
    p = str(v or "").strip().upper()
    return "LIQUID" if p == "WATER" else p


@dataclass(frozen=True)
class PreparedDirectionalScatteringLUT:
    tables: dict[tuple[str, int], dict[tuple[float, float, float, float, float], float]]
    axes: dict[tuple[str, int, str], tuple[float, ...]]


def prepare_directional_scattering_lut(lut: pd.DataFrame | None) -> PreparedDirectionalScatteringLUT | None:
    if lut is None or lut.empty:
        return None
    q = lut.copy()
    q["phase"] = q["phase"].map(_phase)
    for c in ["wavelength_nm", *DIRECTIONAL_INTERPOLATION_AXES, "response_factor"]:
        q[c] = pd.to_numeric(q[c], errors="coerce")
    tables = {}
    axes = {}
    for (phase, wl), g in q.groupby(["phase", q["wavelength_nm"].astype(int)], sort=False):
        key = (str(phase), int(wl))
        tables[key] = {
            (
                float(r.cot), float(r.effective_radius_um), float(r.solar_zenith_deg),
                float(r.view_zenith_deg), float(r.relative_azimuth_deg),
            ): float(r.response_factor)
            for r in g.itertuples(index=False)
        }
        for c in DIRECTIONAL_INTERPOLATION_AXES:
            axes[(str(phase), int(wl), c)] = tuple(sorted(set(float(v) for v in pd.to_numeric(g[c], errors="coerce").dropna().tolist())))
    return PreparedDirectionalScatteringLUT(tables=tables, axes=axes)


def _bracket_values(vals, x: float) -> tuple[float, float] | None:
    vals = sorted(set(float(v) for v in vals))
    if not vals or x < vals[0] or x > vals[-1]:
        return None
    return max(v for v in vals if v <= x), min(v for v in vals if v >= x)


def _axis_weights(lo: float, hi: float, x: float) -> list[tuple[float, float]]:
    if abs(float(hi) - float(lo)) <= 1e-12:
        return [(float(lo), 1.0)]
    t = (float(x) - float(lo)) / (float(hi) - float(lo))
    return [(float(lo), 1.0 - t), (float(hi), t)]


def interpolate_directional_response_factor(
    lut: pd.DataFrame | PreparedDirectionalScatteringLUT,
    *, phase: str, wavelength_nm: int, cot: float, effective_radius_um: float,
    solar_zenith_deg: float, view_zenith_deg: float, relative_azimuth_deg: float,
) -> float:
    """Strict 5-D multilinear interpolation; scattering angle is not an axis."""
    prepared = lut if isinstance(lut, PreparedDirectionalScatteringLUT) else prepare_directional_scattering_lut(lut)
    if prepared is None:
        raise ValueError("DIRECTIONAL_LUT_MISSING")
    key = (_phase(phase), int(wavelength_nm))
    table = prepared.tables.get(key)
    if not table:
        raise ValueError("DIRECTIONAL_LUT_PHASE_WAVELENGTH_MISSING")
    vals = {
        "cot": float(cot), "effective_radius_um": float(effective_radius_um),
        "solar_zenith_deg": float(solar_zenith_deg), "view_zenith_deg": float(view_zenith_deg),
        "relative_azimuth_deg": float(relative_azimuth_deg),
    }
    weighted_axes = []
    for col in DIRECTIONAL_INTERPOLATION_AXES:
        b = _bracket_values(prepared.axes.get((key[0], key[1], col), ()), vals[col])
        if b is None:
            raise ValueError("DIRECTIONAL_LUT_AXIS_OUT_OF_DOMAIN:" + col)
        weighted_axes.append(_axis_weights(b[0], b[1], vals[col]))
    total = weight_total = 0.0
    for corner in itertools.product(*weighted_axes):
        coords = tuple(float(v) for v, _ in corner)
        weight = math.prod(float(w) for _, w in corner)
        if coords not in table:
            raise ValueError("DIRECTIONAL_LUT_LOCAL_CELL_MISSING_CORNER")
        value = table[coords]
        if not _finite(value) or value < 0:
            raise ValueError("DIRECTIONAL_LUT_RESPONSE_FACTOR_INVALID")
        total += weight * value
        weight_total += weight
    if weight_total <= 0 or not _finite(total):
        raise ValueError("DIRECTIONAL_LUT_INTERPOLATION_NUMERIC_FAILURE")
    return float(total / weight_total)


def _bounded_cot_probes(lut: pd.DataFrame | PreparedDirectionalScatteringLUT, *, phase: str, wavelength_nm: int, lo: float, hi: float) -> list[float]:
    if lo > hi:
        lo, hi = hi, lo
    prepared = lut if isinstance(lut, PreparedDirectionalScatteringLUT) else prepare_directional_scattering_lut(lut)
    if prepared is None:
        return []
    vals = list(prepared.axes.get((_phase(phase), int(wavelength_nm), "cot"), ()))
    if not vals or lo < vals[0] or hi > vals[-1]:
        return []
    return sorted({float(lo), float(hi), *[float(v) for v in vals if lo <= v <= hi]})


def _brightness(radiance: dict[int, float | None]) -> float | None:
    if any(not _finite(radiance.get(int(w))) for w in SIX_BAND_WAVELENGTHS_NM):
        return None
    den = sum(_PHOTOPIC_V[int(w)] for w in SIX_BAND_WAVELENGTHS_NM)
    return float(sum(float(radiance[int(w)]) * _PHOTOPIC_V[int(w)] for w in SIX_BAND_WAVELENGTHS_NM) / den) if den > 0 else None


def _redness(radiance: dict[int, float | None]) -> float | None:
    if any(not _finite(radiance.get(int(w))) for w in SIX_BAND_WAVELENGTHS_NM):
        return None
    r = {int(w): float(radiance[int(w)]) for w in SIX_BAND_WAVELENGTHS_NM}
    num = r[650] + r[700] + 0.10 * r[750]
    den = r[550] + r[575] + r[600] + r[650] + r[700] + 0.10 * r[750]
    return 0.0 if den <= 0 else max(0.0, min(1.0, num / den))


def _incident_map(df: pd.DataFrame | None) -> dict[str, pd.Series]:
    if df is None or df.empty:
        return {}
    return {str(r.get("canvas_id")): r for _, r in df.iterrows()}


def build_tier2_directional_scattering_response(
    *, domain: pd.DataFrame, calibrated_lut: pd.DataFrame | None, lut_audit: dict[str, Any] | None,
    cloud_base_illumination: pd.DataFrame | None, prepared_lut: PreparedDirectionalScatteringLUT | None = None,
) -> pd.DataFrame:
    if domain is None or domain.empty:
        return pd.DataFrame(columns=TIER2_DIRECTIONAL_SCATTERING_RESPONSE_COLUMNS)
    audit = dict(lut_audit or {})
    solver_eligible = bool(audit.get("ok")) and bool(audit.get("solver_eligible")) and calibrated_lut is not None and not calibrated_lut.empty
    interp_lut = prepared_lut if prepared_lut is not None else prepare_directional_scattering_lut(calibrated_lut)
    imap = _incident_map(cloud_base_illumination)
    rows = []
    for _, d in domain.iterrows():
        cid = str(d.get("canvas_id")); state = str(d.get("interpolation_domain_state", "UNKNOWN"))
        truth = str(d.get("target_optical_truth_state", "")); sem = str(d.get("target_cot_semantics", "")); phase = _phase(d.get("phase"))
        lo = float(d.get("cot_lower_bound")) if _finite(d.get("cot_lower_bound")) else np.nan
        hi = float(d.get("cot_upper_bound")) if _finite(d.get("cot_upper_bound")) else np.nan
        reff = float(d.get("effective_radius_um")) if _finite(d.get("effective_radius_um")) else np.nan
        theta0 = float(d.get("solar_zenith_deg")) if _finite(d.get("solar_zenith_deg")) else np.nan
        thetav = float(d.get("view_zenith_deg")) if _finite(d.get("view_zenith_deg")) else np.nan
        relaz = float(d.get("relative_azimuth_deg")) if _finite(d.get("relative_azimuth_deg")) else np.nan
        incident = imap.get(cid)
        incvals = {}
        for w in SIX_BAND_WAVELENGTHS_NM:
            v = incident.get(f"relative_base_illumination_{int(w)}nm", np.nan) if incident is not None else np.nan
            incvals[int(w)] = float(v) if _finite(v) else None
        factor = {int(w): None for w in SIX_BAND_WAVELENGTHS_NM}; factor_lo = dict(factor); factor_hi = dict(factor)
        rad = dict(factor); rad_lo = dict(factor); rad_hi = dict(factor)
        executed = False; mode = "NONE"
        if state not in {"INTERPOLATION_DOMAIN_READY_DETERMINISTIC", "INTERPOLATION_DOMAIN_READY_BOUNDED"}:
            execution = "NOT_EXECUTED_DOMAIN_BLOCKED"; response_state = "TIER2_RESPONSE_UNAVAILABLE"; reason = state
        elif not solver_eligible:
            execution = "NOT_EXECUTED_PRODUCTION_CALIBRATION_BLOCKED"; response_state = "TIER2_RESPONSE_UNAVAILABLE"; reason = str(audit.get("production_calibration_state", "PRODUCTION_DIRECTIONAL_CALIBRATION_NOT_READY"))
        elif any(incvals[int(w)] is None for w in SIX_BAND_WAVELENGTHS_NM):
            execution = "NOT_EXECUTED_SIX_BAND_INCIDENT_MISSING"; response_state = "TIER2_RESPONSE_UNAVAILABLE"; reason = "SIX_BAND_CLOUD_BASE_INCIDENT_IRRADIANCE_MISSING"
        else:
            try:
                if state == "INTERPOLATION_DOMAIN_READY_DETERMINISTIC" and truth.startswith("EXACT_") and sem == "EXACT_VALUE":
                    cot = 0.5 * (lo + hi)
                    for w in SIX_BAND_WAVELENGTHS_NM:
                        f = interpolate_directional_response_factor(
                            interp_lut, phase=phase, wavelength_nm=int(w), cot=cot, effective_radius_um=reff,
                            solar_zenith_deg=theta0, view_zenith_deg=thetav, relative_azimuth_deg=relaz,
                        )
                        factor[int(w)] = factor_lo[int(w)] = factor_hi[int(w)] = f
                        rr = max(0.0, float(incvals[int(w)])) * f
                        rad[int(w)] = rad_lo[int(w)] = rad_hi[int(w)] = rr
                    mode = "DETERMINISTIC_5D_FULL_DIRECTIONAL_MULTILINEAR"; execution = "EXECUTED_DETERMINISTIC"; response_state = "READY_TIER2_CALIBRATED_DIRECTIONAL_LUT"; reason = "NONE"; executed = True
                elif state == "INTERPOLATION_DOMAIN_READY_BOUNDED" and truth == "BOUNDED_NATIVE_BRACKET" and sem == "BOUNDED_INTERVAL":
                    for w in SIX_BAND_WAVELENGTHS_NM:
                        probes = _bounded_cot_probes(interp_lut, phase=phase, wavelength_nm=int(w), lo=lo, hi=hi)
                        if not probes:
                            raise ValueError("BOUNDED_COT_PROBES_EMPTY")
                        vals = [
                            interpolate_directional_response_factor(
                                interp_lut, phase=phase, wavelength_nm=int(w), cot=float(c), effective_radius_um=reff,
                                solar_zenith_deg=theta0, view_zenith_deg=thetav, relative_azimuth_deg=relaz,
                            ) for c in probes
                        ]
                        flo, fhi = min(vals), max(vals)
                        factor_lo[int(w)], factor_hi[int(w)] = flo, fhi
                        rad_lo[int(w)] = max(0.0, float(incvals[int(w)])) * flo
                        rad_hi[int(w)] = max(0.0, float(incvals[int(w)])) * fhi
                    mode = "BOUNDED_COT_ENVELOPE_5D_FULL_DIRECTIONAL_MULTILINEAR"; execution = "EXECUTED_BOUNDED_INTERVAL"; response_state = "BOUNDED_TIER2_DIRECTIONAL_RESPONSE_AVAILABLE"; reason = "NONE_BOUNDED_NO_EXACT_RESPONSE"; executed = True
                else:
                    execution = "NOT_EXECUTED_TRUTH_SEMANTICS_BLOCKED"; response_state = "TIER2_RESPONSE_UNAVAILABLE"; reason = truth + ":" + sem
            except Exception as exc:
                execution = "SOLVER_ERROR"; response_state = "TIER2_RESPONSE_UNAVAILABLE"; reason = f"{type(exc).__name__}:{exc}"; executed = False
        b = _brightness(rad); red = _redness(rad); blo = _brightness(rad_lo); bhi = _brightness(rad_hi); rlo = _redness(rad_lo); rhi = _redness(rad_hi)
        row = {
            "time": d.get("time"), "solar_altitude_deg": d.get("solar_altitude_deg"), "canvas_id": d.get("canvas_id"),
            "cloud_layer_id": d.get("cloud_layer_id"), "operational_domain": d.get("operational_domain"), "distance_km": d.get("distance_km"),
            "target_optical_truth_state": truth, "target_cot_semantics": sem, "phase": phase,
            "cot_lower_bound": lo if _finite(lo) else None, "cot_upper_bound": hi if _finite(hi) else None,
            "effective_radius_um": reff if _finite(reff) else None, "cloud_thickness_km": d.get("cloud_thickness_km"),
            "solar_zenith_deg": theta0 if _finite(theta0) else None, "view_zenith_deg": thetav if _finite(thetav) else None,
            "relative_azimuth_deg": relaz if _finite(relaz) else None, "scattering_angle_deg": d.get("scattering_angle_deg"),
            "solar_altitude_target_deg": d.get("solar_altitude_target_deg"), "solar_azimuth_target_deg": d.get("solar_azimuth_target_deg"),
            "view_elevation_deg": d.get("view_elevation_deg"), "view_azimuth_target_deg": d.get("view_azimuth_target_deg"),
            "mu0": d.get("mu0"), "mu_view": d.get("mu_view"), "azimuth_degeneracy_state": d.get("azimuth_degeneracy_state"),
            "lut_runtime_state": str(audit.get("state", "CALIBRATED_DIRECTIONAL_LUT_NOT_INSTALLED")),
            "lut_version": str(audit.get("lut_version", "")), "calibration_id": str(audit.get("calibration_id", "")),
            "calibration_contract": str(audit.get("calibration_contract", "")), "solver_family": str(audit.get("solver_family", "")),
            "solver_version": str(audit.get("solver_version", "")), "response_definition": str(audit.get("response_definition", "")),
            "response_units": str(audit.get("response_units", "")), "interpolation_domain_state": state, "interpolation_mode": mode,
            "solver_execution_state": execution, "response_state": response_state, "blocking_reason": reason,
            "interpolation_executed": bool(executed), "brightness": b, "brightness_lower_bound": blo, "brightness_upper_bound": bhi,
            "redness": red, "redness_lower_bound": rlo, "redness_upper_bound": rhi,
            "cf_or_rh_used_to_infer_cot": False, "solver_contract_version": SOLVER_CONTRACT,
        }
        for w in SIX_BAND_WAVELENGTHS_NM:
            wi = int(w)
            row[f"incident_irradiance_{wi}nm"] = incvals[wi]
            row[f"response_factor_{wi}nm"] = factor[wi]
            row[f"response_factor_{wi}nm_lower_bound"] = factor_lo[wi]
            row[f"response_factor_{wi}nm_upper_bound"] = factor_hi[wi]
            row[f"tier2_radiance_{wi}nm"] = rad[wi]
            row[f"tier2_radiance_{wi}nm_lower_bound"] = rad_lo[wi]
            row[f"tier2_radiance_{wi}nm_upper_bound"] = rad_hi[wi]
        rows.append(row)
    return pd.DataFrame(rows, columns=TIER2_DIRECTIONAL_SCATTERING_RESPONSE_COLUMNS)


def summarize_tier2_directional_scattering_response(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=TIER2_DIRECTIONAL_SCATTERING_RESPONSE_SUMMARY_COLUMNS)
    rows = []
    for angle, g in df.groupby("solar_altitude_deg", sort=False):
        s = g["solver_execution_state"].astype(str)
        det = int(s.eq("EXECUTED_DETERMINISTIC").sum()); bnd = int(s.eq("EXECUTED_BOUNDED_INTERVAL").sum())
        if det or bnd:
            closure = "TIER2_DIRECTIONAL_RESPONSE_AVAILABLE"
        elif s.eq("NOT_EXECUTED_PRODUCTION_CALIBRATION_BLOCKED").any():
            closure = "PRODUCTION_DIRECTIONAL_CALIBRATION_BLOCKED"
        elif s.eq("SOLVER_ERROR").any():
            closure = "SOLVER_ERROR"
        else:
            closure = "TARGET_OR_DIRECTIONAL_DOMAIN_BLOCKED"
        rows.append({
            "solar_altitude_deg": float(angle), "canvas_count": int(len(g)),
            "deterministic_response_count": det, "bounded_response_count": bnd,
            "domain_blocked_count": int(s.eq("NOT_EXECUTED_DOMAIN_BLOCKED").sum()),
            "production_calibration_blocked_count": int(s.eq("NOT_EXECUTED_PRODUCTION_CALIBRATION_BLOCKED").sum()),
            "incident_missing_count": int(s.eq("NOT_EXECUTED_SIX_BAND_INCIDENT_MISSING").sum()),
            "solver_error_count": int(s.eq("SOLVER_ERROR").sum()),
            "interpolation_executed_count": int(g["interpolation_executed"].fillna(False).astype(bool).sum()),
            "closure_state": closure, "solver_contract_version": SOLVER_CONTRACT,
        })
    return pd.DataFrame(rows, columns=TIER2_DIRECTIONAL_SCATTERING_RESPONSE_SUMMARY_COLUMNS)


def mark_directional_domain_interpolation_execution(domain: pd.DataFrame, response: pd.DataFrame) -> pd.DataFrame:
    if domain is None or domain.empty:
        return domain.copy() if isinstance(domain, pd.DataFrame) else pd.DataFrame()
    out = domain.copy()
    if response is None or response.empty:
        return out
    executed = {str(r.get("canvas_id")): bool(r.get("interpolation_executed", False)) for _, r in response.iterrows()}
    out["interpolation_executed"] = [executed.get(str(cid), False) for cid in out["canvas_id"]]
    return out
