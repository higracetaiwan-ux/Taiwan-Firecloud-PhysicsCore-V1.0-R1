from __future__ import annotations

"""Portable Ice Optics consumer package for WINDY Firecloud Observer.

R5.7.41.3.4.10.11.2 preserves the runtime-decoupled architecture introduced
in R5.7.41.3.4.10.10.1 while correcting the authoritative size coordinate.

* PhysicsCore remains the authoring/calibration/validation authority.
* WINDY remains a standalone consumer with no PhysicsCore/Python/Streamlit
  runtime dependency.
* The authoritative Yang/Bi V2 portable lookup axis is now maximum particle
  dimension (Dmax), not the source-row-derived effective-radius diagnostic.
* No r_eff -> Dmax conversion is fabricated.  If a consumer has no calibrated
  Dmax input/mapping, positive-IWP optics fail closed.

This module does not promote Ice Optics into Formation, Viewing, Twilight Glow,
Red-Light, COT, or any other frozen production physics branch.
"""

from dataclasses import asdict
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from typing import Any, Mapping
import json
import math
import zipfile

import numpy as np
import pandas as pd

from .ice_cloud_spectral_optics import (
    ICE_OPTICS_CONTRACT_VERSION,
    ICE_OPTICS_WAVELENGTHS_NM,
    IceOpticsLUTStatus,
    validate_ice_optics_lut,
)

PORTABLE_PACKAGE_CONTRACT_VERSION = "FIRECLOUD_ICE_OPTICS_PORTABLE_V1_1"
PORTABLE_PACKAGE_SCHEMA_VERSION = 2
PORTABLE_RUNTIME_DEPENDENCY = "NONE"
PORTABLE_CONSUMER = "WINDY_FIRECLOUD_OBSERVER"
PORTABLE_EVALUATOR_VERSION = "ICE_OPTICS_EVALUATOR_V1_1"
PORTABLE_PRIMARY_SIZE_COORDINATE = "maximum_dimension_um"


def _json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True, default=str).encode("utf-8")


def _csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, lineterminator="\n").encode("utf-8")


def _sha(payload: bytes) -> str:
    return sha256(payload).hexdigest()


def _portable_lut_records(lut: pd.DataFrame) -> list[dict[str, Any]]:
    df = validate_ice_optics_lut(lut, require_full_six_band=True)
    records: list[dict[str, Any]] = []
    for rec in df.to_dict(orient="records"):
        records.append({
            "wavelength_nm": int(round(float(rec["wavelength_nm"]))),
            "maximum_dimension_um": float(rec["maximum_dimension_um"]),
            # These are retained as source-row-derived diagnostics.  They are
            # not the portable runtime lookup axis in V1.1.
            "effective_diameter_um": float(rec["effective_diameter_um"]),
            "effective_radius_um": float(rec["effective_radius_um"]),
            "ice_habit": str(rec["ice_habit"]),
            "surface_roughness": str(rec["surface_roughness"]),
            "mass_extinction_coefficient_m2_kg": float(rec["mass_extinction_coefficient_m2_kg"]),
            "single_scattering_albedo": float(rec["single_scattering_albedo"]),
            "asymmetry_parameter": float(rec["asymmetry_parameter"]),
            "source_dataset": str(rec["source_dataset"]),
            "source_version": str(rec["source_version"]),
            "source_record_provenance": str(rec["source_record_provenance"]),
        })
    return records


def _lookup_group(
    lut: pd.DataFrame,
    habit: str,
    roughness: str,
    maximum_dimension_um: float,
) -> tuple[pd.DataFrame, str]:
    """Lookup/interpolate six bands on the authoritative Dmax axis.

    Interpolation is allowed only between tabulated Dmax nodes within the same
    habit and roughness state.  No habit/roughness interpolation and no
    extrapolation are permitted.
    """
    df = validate_ice_optics_lut(lut, require_full_six_band=True)
    sub = df[
        df["ice_habit"].astype(str).eq(str(habit))
        & df["surface_roughness"].astype(str).eq(str(roughness))
    ].copy()
    if sub.empty:
        return pd.DataFrame(), "ICE_HABIT_ROUGHNESS_NOT_IN_LUT"

    dims = np.array(
        sorted(pd.to_numeric(sub["maximum_dimension_um"], errors="coerce").dropna().unique()),
        dtype=float,
    )
    if len(dims) == 0 or not math.isfinite(float(maximum_dimension_um)):
        return pd.DataFrame(), "ICE_MAXIMUM_DIMENSION_MISSING"

    d = float(maximum_dimension_um)
    if d < dims.min() - 1e-12 or d > dims.max() + 1e-12:
        return pd.DataFrame(), "ICE_DMAX_OUTSIDE_LUT_DOMAIN"

    exact = np.where(np.isclose(dims, d, rtol=0.0, atol=1e-9))[0]
    if len(exact):
        dd = float(dims[int(exact[0])])
        out = sub[
            np.isclose(pd.to_numeric(sub["maximum_dimension_um"], errors="coerce"), dd, atol=1e-9, rtol=0.0)
        ].copy()
        if set(out["wavelength_nm"].round().astype(int)) != set(ICE_OPTICS_WAVELENGTHS_NM):
            return pd.DataFrame(), "ICE_LUT_SIX_BAND_GROUP_INCOMPLETE"
        return out, "EXACT_DMAX_LUT_ROW"

    hi = int(np.searchsorted(dims, d, side="right"))
    lo = hi - 1
    if lo < 0 or hi >= len(dims):
        return pd.DataFrame(), "ICE_DMAX_OUTSIDE_LUT_DOMAIN"
    d0, d1 = float(dims[lo]), float(dims[hi])
    a = sub[
        np.isclose(pd.to_numeric(sub["maximum_dimension_um"], errors="coerce"), d0, atol=1e-9, rtol=0.0)
    ].set_index("wavelength_nm")
    b = sub[
        np.isclose(pd.to_numeric(sub["maximum_dimension_um"], errors="coerce"), d1, atol=1e-9, rtol=0.0)
    ].set_index("wavelength_nm")
    required = set(ICE_OPTICS_WAVELENGTHS_NM)
    if set(a.index.astype(int)) != required or set(b.index.astype(int)) != required:
        return pd.DataFrame(), "ICE_LUT_SIX_BAND_GROUP_INCOMPLETE"

    w = (d - d0) / (d1 - d0)
    rows: list[dict[str, Any]] = []
    for wl in ICE_OPTICS_WAVELENGTHS_NM:
        x = a.loc[wl]
        y = b.loc[wl]

        def lerp(col: str) -> float:
            return float(x[col] + w * (y[col] - x[col]))

        rows.append({
            "wavelength_nm": int(wl),
            "maximum_dimension_um": d,
            "effective_diameter_um": lerp("effective_diameter_um"),
            "effective_radius_um": lerp("effective_radius_um"),
            "ice_habit": str(habit),
            "surface_roughness": str(roughness),
            "mass_extinction_coefficient_m2_kg": lerp("mass_extinction_coefficient_m2_kg"),
            "single_scattering_albedo": lerp("single_scattering_albedo"),
            "asymmetry_parameter": lerp("asymmetry_parameter"),
        })
    return pd.DataFrame(rows), "LINEAR_DMAX_INTERPOLATION_WITHIN_LUT"


def evaluate_portable_ice_optics(
    lut: pd.DataFrame,
    *,
    iwp_kg_m2: float | None,
    native_vertical_completeness: float | None,
    maximum_dimension_um: float | None,
    ice_habit: str | None,
    surface_roughness: str | None,
) -> dict[str, Any]:
    """Reference evaluator mirrored by the standalone JS/TS package.

    Dmax is intentionally explicit.  Positive-IWP rows fail closed when Dmax,
    habit, roughness, or six-band LUT support is unavailable.
    """
    base: dict[str, Any] = {
        "evaluator_version": PORTABLE_EVALUATOR_VERSION,
        "contract_version": ICE_OPTICS_CONTRACT_VERSION,
        "portable_contract_version": PORTABLE_PACKAGE_CONTRACT_VERSION,
        "state": "UNKNOWN",
        "missing_reason": "",
        "iwp_kg_m2": None if iwp_kg_m2 is None else float(iwp_kg_m2),
        "native_vertical_completeness": None if native_vertical_completeness is None else float(native_vertical_completeness),
        "maximum_dimension_um": None if maximum_dimension_um is None else float(maximum_dimension_um),
        "ice_habit": str(ice_habit or "UNKNOWN"),
        "surface_roughness": str(surface_roughness or "UNKNOWN"),
        "bands": {},
    }
    if iwp_kg_m2 is None or not math.isfinite(float(iwp_kg_m2)):
        base.update(state="ICE_IWP_MISSING", missing_reason="NATIVE_IWP_MISSING")
        return base
    if (
        native_vertical_completeness is None
        or not math.isfinite(float(native_vertical_completeness))
        or float(native_vertical_completeness) < 1.0 - 1e-12
    ):
        base.update(
            state="ICE_IWP_INCOMPLETE_NATIVE_VERTICAL_SUPPORT",
            missing_reason="NATIVE_VERTICAL_COMPLETENESS_LT_1",
        )
        return base
    iwp = float(iwp_kg_m2)
    if iwp < 0.0:
        base.update(state="ICE_IWP_INVALID", missing_reason="NEGATIVE_IWP")
        return base
    if abs(iwp) <= 1e-15:
        base["state"] = "NO_ICE_CONDENSATE_AT_NATIVE_STATE"
        for wl in ICE_OPTICS_WAVELENGTHS_NM:
            base["bands"][str(wl)] = {
                "k_ext_m2_kg": None,
                "tau": 0.0,
                "transmission": 1.0,
                "ssa": None,
                "g": None,
                "source_effective_radius_um": None,
            }
        return base
    if maximum_dimension_um is None or not math.isfinite(float(maximum_dimension_um)):
        base.update(state="ICE_MAXIMUM_DIMENSION_MISSING", missing_reason="NO_NATIVE_OR_CALIBRATED_ICE_DMAX")
        return base
    if not ice_habit or str(ice_habit).strip().upper() == "UNKNOWN":
        base.update(state="ICE_HABIT_MISSING", missing_reason="NO_NATIVE_OR_CALIBRATED_ICE_HABIT")
        return base
    if not surface_roughness or str(surface_roughness).strip().upper() == "UNKNOWN":
        base.update(state="ICE_ROUGHNESS_MISSING", missing_reason="NO_CALIBRATED_ICE_ROUGHNESS")
        return base

    rows, state = _lookup_group(
        lut,
        str(ice_habit),
        str(surface_roughness),
        float(maximum_dimension_um),
    )
    if rows.empty:
        base.update(state=state, missing_reason=state)
        return base

    base["state"] = "ICE_SIX_BAND_OPTICS_READY"
    base["lookup_state"] = state
    for _, row in rows.iterrows():
        wl = int(row["wavelength_nm"])
        k = float(row["mass_extinction_coefficient_m2_kg"])
        tau = iwp * k
        base["bands"][str(wl)] = {
            "k_ext_m2_kg": k,
            "tau": tau,
            "transmission": math.exp(-tau),
            "ssa": float(row["single_scattering_albedo"]),
            "g": float(row["asymmetry_parameter"]),
            "source_effective_radius_um": float(row["effective_radius_um"]),
        }
    return base


def build_reference_validation_vectors(lut: pd.DataFrame) -> dict[str, Any]:
    """Create deterministic Dmax-axis cross-language software vectors."""
    df = validate_ice_optics_lut(lut, require_full_six_band=True)
    groups = list(df.groupby(["ice_habit", "surface_roughness"], sort=True))
    if not groups:
        raise ValueError("calibrated ice optics LUT has no habit/roughness groups")

    vectors: list[dict[str, Any]] = []
    case_id = 0
    for (habit, roughness), g in groups[:3]:
        dims = sorted(pd.to_numeric(g["maximum_dimension_um"], errors="coerce").dropna().unique().tolist())
        if not dims:
            continue
        candidates = [float(dims[0]), float(dims[-1])]
        if len(dims) >= 2:
            candidates.insert(1, (float(dims[0]) + float(dims[-1])) / 2.0)
        for dmax in candidates:
            case_id += 1
            inp = {
                "iwp_kg_m2": 0.01,
                "native_vertical_completeness": 1.0,
                "maximum_dimension_um": float(dmax),
                "ice_habit": str(habit),
                "surface_roughness": str(roughness),
            }
            expected = evaluate_portable_ice_optics(df, **inp)
            vectors.append({
                "case_id": f"READY_{case_id:03d}",
                "purpose": "SOFTWARE_VALIDATION_ONLY",
                "input": inp,
                "expected": expected,
            })

    zero = {
        "iwp_kg_m2": 0.0,
        "native_vertical_completeness": 1.0,
        "maximum_dimension_um": None,
        "ice_habit": None,
        "surface_roughness": None,
    }
    vectors.append({
        "case_id": "EXACT_ZERO_IWP",
        "purpose": "SOFTWARE_VALIDATION_ONLY",
        "input": zero,
        "expected": evaluate_portable_ice_optics(df, **zero),
    })
    incomplete = {
        "iwp_kg_m2": 0.01,
        "native_vertical_completeness": 0.5,
        "maximum_dimension_um": None,
        "ice_habit": None,
        "surface_roughness": None,
    }
    vectors.append({
        "case_id": "INCOMPLETE_VERTICAL_SUPPORT",
        "purpose": "SOFTWARE_VALIDATION_ONLY",
        "input": incomplete,
        "expected": evaluate_portable_ice_optics(df, **incomplete),
    })
    missing_dmax = {
        "iwp_kg_m2": 0.01,
        "native_vertical_completeness": 1.0,
        "maximum_dimension_um": None,
        "ice_habit": str(groups[0][0][0]),
        "surface_roughness": str(groups[0][0][1]),
    }
    vectors.append({
        "case_id": "POSITIVE_IWP_DMAX_MISSING_FAIL_CLOSED",
        "purpose": "SOFTWARE_VALIDATION_ONLY",
        "input": missing_dmax,
        "expected": evaluate_portable_ice_optics(df, **missing_dmax),
    })
    return {
        "validation_contract": "FIRECLOUD_ICE_OPTICS_CROSS_LANGUAGE_V1_1",
        "evaluator_version": PORTABLE_EVALUATOR_VERSION,
        "primary_size_coordinate": PORTABLE_PRIMARY_SIZE_COORDINATE,
        "purpose": "Cross-language software parity only; not meteorological calibration.",
        "vectors": vectors,
    }


def portable_contract_payload(*, physicscore_version: str, science_baseline: str) -> dict[str, Any]:
    return {
        "portable_package_contract_version": PORTABLE_PACKAGE_CONTRACT_VERSION,
        "schema_version": PORTABLE_PACKAGE_SCHEMA_VERSION,
        "ice_optics_contract_version": ICE_OPTICS_CONTRACT_VERSION,
        "evaluator_version": PORTABLE_EVALUATOR_VERSION,
        "physicscore_authoring_version": str(physicscore_version),
        "science_baseline": str(science_baseline),
        "consumer": PORTABLE_CONSUMER,
        "runtime_dependency_on_physicscore": PORTABLE_RUNTIME_DEPENDENCY,
        "runtime_dependency_on_python": "NONE",
        "runtime_dependency_on_streamlit": "NONE",
        "wavelengths_nm": list(ICE_OPTICS_WAVELENGTHS_NM),
        "primary_size_coordinate": PORTABLE_PRIMARY_SIZE_COORDINATE,
        "interpolation": {
            "wavelength": "NONE_AT_RUNTIME_LUT_ALREADY_NORMALIZED_TO_SIX_BANDS",
            "maximum_dimension": "LINEAR_WITHIN_SAME_HABIT_AND_ROUGHNESS_ONLY",
            "effective_radius": "DIAGNOSTIC_ONLY_NOT_RUNTIME_LOOKUP_AXIS",
            "habit": "NO_INTERPOLATION",
            "surface_roughness": "NO_INTERPOLATION",
            "extrapolation": "PROHIBITED",
        },
        "equations": {
            "tau": "tau_ice_lambda = IWP_kg_m2 * k_ext_ice_lambda_m2_kg",
            "transmission": "T_ice_lambda = exp(-tau_ice_lambda)",
        },
        "missing_semantics": (
            "Missing != Clear != Zero; positive IWP requires complete vertical support, calibrated Dmax, "
            "habit, roughness and LUT domain coverage. No r_eff-to-Dmax substitution is permitted."
        ),
        "effective_radius_semantics": (
            "Source-row-derived diagnostic/mapping metadata only; wavelength-dependent values are preserved and "
            "must not be treated as the authoritative six-band lookup key."
        ),
        "consumer_input_caveat": (
            "If WINDY does not have native/calibrated Dmax or a separately validated microphysics mapping, "
            "the evaluator must return ICE_MAXIMUM_DIMENSION_MISSING for positive IWP."
        ),
        "deployment_boundary": (
            "PhysicsCore builds/calibrates/certifies the package; WINDY imports the released artifact and evaluates "
            "locally without calling PhysicsCore."
        ),
        "physics_promotion_allowed": False,
    }


REFERENCE_EVALUATOR_MJS = r'''// Firecloud Ice Optics portable Dmax-first reference evaluator.
// Dependency-free ES module. No PhysicsCore/Python/Streamlit runtime dependency.
export const WAVELENGTHS_NM = [550,575,600,650,700,750];
export const EVALUATOR_VERSION = "ICE_OPTICS_EVALUATOR_V1_1";
export const PORTABLE_CONTRACT_VERSION = "FIRECLOUD_ICE_OPTICS_PORTABLE_V1_1";
const finite = (x) => x !== null && x !== undefined && x !== '' && Number.isFinite(Number(x));
const approx = (a,b,tol=1e-9) => Math.abs(Number(a)-Number(b)) <= tol;
function groupRows(lut, habit, roughness) {
  return lut.filter(r => String(r.ice_habit) === String(habit) && String(r.surface_roughness) === String(roughness));
}
function lookup(lut, habit, roughness, dmax) {
  const sub = groupRows(lut, habit, roughness);
  if (!sub.length) return {state:"ICE_HABIT_ROUGHNESS_NOT_IN_LUT", rows:[]};
  const dims = [...new Set(sub.map(r => Number(r.maximum_dimension_um)))].filter(Number.isFinite).sort((a,b)=>a-b);
  if (!finite(dmax)) return {state:"ICE_MAXIMUM_DIMENSION_MISSING", rows:[]};
  const d = Number(dmax);
  if (!dims.length || d < dims[0]-1e-12 || d > dims[dims.length-1]+1e-12) return {state:"ICE_DMAX_OUTSIDE_LUT_DOMAIN", rows:[]};
  const exact = dims.find(x => approx(x,d));
  if (exact !== undefined) {
    const rows = sub.filter(x=>approx(x.maximum_dimension_um,exact));
    if (new Set(rows.map(x=>Number(x.wavelength_nm))).size !== WAVELENGTHS_NM.length) return {state:"ICE_LUT_SIX_BAND_GROUP_INCOMPLETE",rows:[]};
    return {state:"EXACT_DMAX_LUT_ROW", rows};
  }
  const hi = dims.findIndex(x => x > d), lo = hi - 1;
  if (lo < 0 || hi < 0) return {state:"ICE_DMAX_OUTSIDE_LUT_DOMAIN", rows:[]};
  const d0=dims[lo], d1=dims[hi], w=(d-d0)/(d1-d0), out=[];
  for (const wl of WAVELENGTHS_NM) {
    const a=sub.find(x=>Number(x.wavelength_nm)===wl && approx(x.maximum_dimension_um,d0));
    const b=sub.find(x=>Number(x.wavelength_nm)===wl && approx(x.maximum_dimension_um,d1));
    if (!a || !b) return {state:"ICE_LUT_SIX_BAND_GROUP_INCOMPLETE", rows:[]};
    const lerp=(x,y)=>Number(x)+w*(Number(y)-Number(x));
    out.push({
      wavelength_nm:wl, maximum_dimension_um:d,
      effective_diameter_um:lerp(a.effective_diameter_um,b.effective_diameter_um),
      effective_radius_um:lerp(a.effective_radius_um,b.effective_radius_um),
      ice_habit:String(habit), surface_roughness:String(roughness),
      mass_extinction_coefficient_m2_kg:lerp(a.mass_extinction_coefficient_m2_kg,b.mass_extinction_coefficient_m2_kg),
      single_scattering_albedo:lerp(a.single_scattering_albedo,b.single_scattering_albedo),
      asymmetry_parameter:lerp(a.asymmetry_parameter,b.asymmetry_parameter)
    });
  }
  return {state:"LINEAR_DMAX_INTERPOLATION_WITHIN_LUT", rows:out};
}
export function evaluateIceOptics(input, lut) {
  const iwp=input?.iwp_kg_m2, vc=input?.native_vertical_completeness, dmax=input?.maximum_dimension_um;
  const habit=input?.ice_habit ?? "UNKNOWN", rough=input?.surface_roughness ?? "UNKNOWN";
  const out={
    evaluator_version:EVALUATOR_VERSION, contract_version:"FIRECLOUD_ICE_OPTICS_V1",
    portable_contract_version:PORTABLE_CONTRACT_VERSION, state:"UNKNOWN", missing_reason:"",
    iwp_kg_m2:finite(iwp)?Number(iwp):null, native_vertical_completeness:finite(vc)?Number(vc):null,
    maximum_dimension_um:finite(dmax)?Number(dmax):null, ice_habit:String(habit||"UNKNOWN"),
    surface_roughness:String(rough||"UNKNOWN"), bands:{}
  };
  if (!finite(iwp)) {out.state="ICE_IWP_MISSING";out.missing_reason="NATIVE_IWP_MISSING";return out;}
  if (!finite(vc) || Number(vc)<1-1e-12) {out.state="ICE_IWP_INCOMPLETE_NATIVE_VERTICAL_SUPPORT";out.missing_reason="NATIVE_VERTICAL_COMPLETENESS_LT_1";return out;}
  if (Number(iwp)<0) {out.state="ICE_IWP_INVALID";out.missing_reason="NEGATIVE_IWP";return out;}
  if (Math.abs(Number(iwp))<=1e-15) {out.state="NO_ICE_CONDENSATE_AT_NATIVE_STATE";for(const wl of WAVELENGTHS_NM)out.bands[String(wl)]={k_ext_m2_kg:null,tau:0,transmission:1,ssa:null,g:null,source_effective_radius_um:null};return out;}
  if (!finite(dmax)) {out.state="ICE_MAXIMUM_DIMENSION_MISSING";out.missing_reason="NO_NATIVE_OR_CALIBRATED_ICE_DMAX";return out;}
  if (!habit || String(habit).toUpperCase()==="UNKNOWN") {out.state="ICE_HABIT_MISSING";out.missing_reason="NO_NATIVE_OR_CALIBRATED_ICE_HABIT";return out;}
  if (!rough || String(rough).toUpperCase()==="UNKNOWN") {out.state="ICE_ROUGHNESS_MISSING";out.missing_reason="NO_CALIBRATED_ICE_ROUGHNESS";return out;}
  const found=lookup(lut,String(habit),String(rough),Number(dmax));
  if (!found.rows.length) {out.state=found.state;out.missing_reason=found.state;return out;}
  out.state="ICE_SIX_BAND_OPTICS_READY";out.lookup_state=found.state;
  for(const r of found.rows){const wl=Number(r.wavelength_nm),k=Number(r.mass_extinction_coefficient_m2_kg),tau=Number(iwp)*k;out.bands[String(wl)]={k_ext_m2_kg:k,tau,transmission:Math.exp(-tau),ssa:Number(r.single_scattering_albedo),g:Number(r.asymmetry_parameter),source_effective_radius_um:Number(r.effective_radius_um)};}
  return out;
}
'''


REFERENCE_EVALUATOR_TS = r'''// Firecloud Ice Optics portable Dmax-first TypeScript evaluator for WINDY/Svelte.
export const WAVELENGTHS_NM = [550,575,600,650,700,750] as const;
export const EVALUATOR_VERSION = "ICE_OPTICS_EVALUATOR_V1_1";
export const PORTABLE_CONTRACT_VERSION = "FIRECLOUD_ICE_OPTICS_PORTABLE_V1_1";
export type IceOpticsInput = { iwp_kg_m2:number|null; native_vertical_completeness:number|null; maximum_dimension_um:number|null; ice_habit:string|null; surface_roughness:string|null };
export type IceLutRow = { wavelength_nm:number; maximum_dimension_um:number; effective_diameter_um:number; effective_radius_um:number; ice_habit:string; surface_roughness:string; mass_extinction_coefficient_m2_kg:number; single_scattering_albedo:number; asymmetry_parameter:number; [key:string]:unknown };
export type IceBandResult = { k_ext_m2_kg:number|null; tau:number; transmission:number; ssa:number|null; g:number|null; source_effective_radius_um:number|null };
export type IceOpticsResult = { evaluator_version:string; contract_version:string; portable_contract_version:string; state:string; missing_reason:string; iwp_kg_m2:number|null; native_vertical_completeness:number|null; maximum_dimension_um:number|null; ice_habit:string; surface_roughness:string; lookup_state?:string; bands:Record<string,IceBandResult> };
const finite=(x:unknown):boolean => x !== null && x !== undefined && x !== '' && Number.isFinite(Number(x));
const approx=(a:unknown,b:unknown,tol=1e-9):boolean => Math.abs(Number(a)-Number(b)) <= tol;
function groupRows(lut:IceLutRow[], habit:string, roughness:string):IceLutRow[]{return lut.filter(r=>String(r.ice_habit)===String(habit)&&String(r.surface_roughness)===String(roughness));}
function lookup(lut:IceLutRow[],habit:string,roughness:string,dmax:number):{state:string;rows:IceLutRow[]}{
  const sub=groupRows(lut,habit,roughness); if(!sub.length)return{state:"ICE_HABIT_ROUGHNESS_NOT_IN_LUT",rows:[]};
  const dims=[...new Set(sub.map(r=>Number(r.maximum_dimension_um)))].filter(Number.isFinite).sort((a,b)=>a-b);
  if(!finite(dmax))return{state:"ICE_MAXIMUM_DIMENSION_MISSING",rows:[]};
  const d=Number(dmax); if(!dims.length||d<dims[0]-1e-12||d>dims[dims.length-1]+1e-12)return{state:"ICE_DMAX_OUTSIDE_LUT_DOMAIN",rows:[]};
  const exact=dims.find(x=>approx(x,d)); if(exact!==undefined){const rows=sub.filter(x=>approx(x.maximum_dimension_um,exact));if(new Set(rows.map(x=>Number(x.wavelength_nm))).size!==WAVELENGTHS_NM.length)return{state:"ICE_LUT_SIX_BAND_GROUP_INCOMPLETE",rows:[]};return{state:"EXACT_DMAX_LUT_ROW",rows};}
  const hi=dims.findIndex(x=>x>d),lo=hi-1; if(lo<0||hi<0)return{state:"ICE_DMAX_OUTSIDE_LUT_DOMAIN",rows:[]};
  const d0=dims[lo],d1=dims[hi],w=(d-d0)/(d1-d0),out:IceLutRow[]=[];
  for(const wl of WAVELENGTHS_NM){
    const a=sub.find(x=>Number(x.wavelength_nm)===wl&&approx(x.maximum_dimension_um,d0)); const b=sub.find(x=>Number(x.wavelength_nm)===wl&&approx(x.maximum_dimension_um,d1));
    if(!a||!b)return{state:"ICE_LUT_SIX_BAND_GROUP_INCOMPLETE",rows:[]}; const lerp=(x:unknown,y:unknown)=>Number(x)+w*(Number(y)-Number(x));
    out.push({wavelength_nm:wl,maximum_dimension_um:d,effective_diameter_um:lerp(a.effective_diameter_um,b.effective_diameter_um),effective_radius_um:lerp(a.effective_radius_um,b.effective_radius_um),ice_habit:String(habit),surface_roughness:String(roughness),mass_extinction_coefficient_m2_kg:lerp(a.mass_extinction_coefficient_m2_kg,b.mass_extinction_coefficient_m2_kg),single_scattering_albedo:lerp(a.single_scattering_albedo,b.single_scattering_albedo),asymmetry_parameter:lerp(a.asymmetry_parameter,b.asymmetry_parameter)});
  }
  return{state:"LINEAR_DMAX_INTERPOLATION_WITHIN_LUT",rows:out};
}
export function evaluateIceOptics(input:IceOpticsInput,lut:IceLutRow[]):IceOpticsResult{
  const iwp=input?.iwp_kg_m2,vc=input?.native_vertical_completeness,dmax=input?.maximum_dimension_um,habit=input?.ice_habit??"UNKNOWN",rough=input?.surface_roughness??"UNKNOWN";
  const out:IceOpticsResult={evaluator_version:EVALUATOR_VERSION,contract_version:"FIRECLOUD_ICE_OPTICS_V1",portable_contract_version:PORTABLE_CONTRACT_VERSION,state:"UNKNOWN",missing_reason:"",iwp_kg_m2:finite(iwp)?Number(iwp):null,native_vertical_completeness:finite(vc)?Number(vc):null,maximum_dimension_um:finite(dmax)?Number(dmax):null,ice_habit:String(habit||"UNKNOWN"),surface_roughness:String(rough||"UNKNOWN"),bands:{}};
  if(!finite(iwp)){out.state="ICE_IWP_MISSING";out.missing_reason="NATIVE_IWP_MISSING";return out;}
  if(!finite(vc)||Number(vc)<1-1e-12){out.state="ICE_IWP_INCOMPLETE_NATIVE_VERTICAL_SUPPORT";out.missing_reason="NATIVE_VERTICAL_COMPLETENESS_LT_1";return out;}
  if(Number(iwp)<0){out.state="ICE_IWP_INVALID";out.missing_reason="NEGATIVE_IWP";return out;}
  if(Math.abs(Number(iwp))<=1e-15){out.state="NO_ICE_CONDENSATE_AT_NATIVE_STATE";for(const wl of WAVELENGTHS_NM)out.bands[String(wl)]={k_ext_m2_kg:null,tau:0,transmission:1,ssa:null,g:null,source_effective_radius_um:null};return out;}
  if(!finite(dmax)){out.state="ICE_MAXIMUM_DIMENSION_MISSING";out.missing_reason="NO_NATIVE_OR_CALIBRATED_ICE_DMAX";return out;}
  if(!habit||String(habit).toUpperCase()==="UNKNOWN"){out.state="ICE_HABIT_MISSING";out.missing_reason="NO_NATIVE_OR_CALIBRATED_ICE_HABIT";return out;}
  if(!rough||String(rough).toUpperCase()==="UNKNOWN"){out.state="ICE_ROUGHNESS_MISSING";out.missing_reason="NO_CALIBRATED_ICE_ROUGHNESS";return out;}
  const found=lookup(lut,String(habit),String(rough),Number(dmax)); if(!found.rows.length){out.state=found.state;out.missing_reason=found.state;return out;}
  out.state="ICE_SIX_BAND_OPTICS_READY";out.lookup_state=found.state;
  for(const r of found.rows){const wl=Number(r.wavelength_nm),k=Number(r.mass_extinction_coefficient_m2_kg),tau=Number(iwp)*k;out.bands[String(wl)]={k_ext_m2_kg:k,tau,transmission:Math.exp(-tau),ssa:Number(r.single_scattering_albedo),g:Number(r.asymmetry_parameter),source_effective_radius_um:Number(r.effective_radius_um)};}
  return out;
}
'''


VALIDATE_PACKAGE_MJS = r'''import fs from 'node:fs';
import {evaluateIceOptics} from '../windy/iceOpticsEvaluator.mjs';
const lut=JSON.parse(fs.readFileSync(new URL('../ice_optics_lut_v1.json', import.meta.url),'utf8')).records;
const v=JSON.parse(fs.readFileSync(new URL('./reference_vectors.json', import.meta.url),'utf8'));
const close=(a,b,t=1e-10)=>a===b || (Number.isFinite(a)&&Number.isFinite(b)&&Math.abs(a-b)<=t*Math.max(1,Math.abs(a),Math.abs(b)));
function eq(a,b,path='root') { if (typeof a==='number'||typeof b==='number') {if(!close(a,b)) throw new Error(`${path}: ${a} != ${b}`);return;} if(a===null||b===null||typeof a!=='object'||typeof b!=='object'){if(a!==b)throw new Error(`${path}: ${a} != ${b}`);return;} for(const k of new Set([...Object.keys(a),...Object.keys(b)]))eq(a[k],b[k],`${path}.${k}`); }
for(const x of v.vectors){const got=evaluateIceOptics(x.input,lut);eq(got,x.expected,x.case_id);}
console.log(`PASS ${v.vectors.length} vectors`);
'''


README_WINDY = """# Firecloud Ice Optics Portable Package — Dmax-first V1.1

This package is a released science artifact generated and validated by Taiwan Firecloud PhysicsCore.

**Runtime architecture:** WINDY does not call PhysicsCore. WINDY loads `ice_optics_lut_v1.json` (or CSV) and evaluates locally with `windy/iceOpticsEvaluator.mjs` or an equivalent TypeScript port.

Rules:
- fixed bands: 550/575/600/650/700/750 nm
- authoritative runtime size axis: `maximum_dimension_um` (Dmax)
- `effective_radius_um` is source-row-derived diagnostic/mapping metadata, not the six-band lookup key
- `tau_ice = IWP * k_ext`
- `T = exp(-tau)`
- Dmax interpolation only within the same habit + roughness
- no Dmax extrapolation; no habit/roughness interpolation
- Missing != Clear != Zero
- positive IWP never receives a fabricated Dmax, r_eff->Dmax conversion, habit, roughness, or k_ext

If WINDY does not have a native/calibrated Dmax or a separately validated microphysics mapping, positive-IWP evaluation must remain `ICE_MAXIMUM_DIMENSION_MISSING`.

Before a WINDY release, run `node validation/validatePackage.mjs`.
"""


def build_portable_package_files(
    lut: pd.DataFrame,
    *,
    physicscore_version: str,
    science_baseline: str,
    lut_status: IceOpticsLUTStatus | None = None,
    source_manifest: Mapping[str, Any] | None = None,
) -> dict[str, bytes]:
    df = validate_ice_optics_lut(lut, require_full_six_band=True)
    if df.empty:
        raise ValueError("portable package requires a non-empty calibrated six-band LUT")
    records = _portable_lut_records(df)
    lut_json_obj = {
        "ice_optics_contract_version": ICE_OPTICS_CONTRACT_VERSION,
        "portable_package_contract_version": PORTABLE_PACKAGE_CONTRACT_VERSION,
        "primary_size_coordinate": PORTABLE_PRIMARY_SIZE_COORDINATE,
        "wavelengths_nm": list(ICE_OPTICS_WAVELENGTHS_NM),
        "row_count": len(records),
        "records": records,
    }
    vectors = build_reference_validation_vectors(df)
    contract = portable_contract_payload(
        physicscore_version=physicscore_version,
        science_baseline=science_baseline,
    )
    files: dict[str, bytes] = {
        "ice_optics_lut_v1.csv": _csv_bytes(df),
        "ice_optics_lut_v1.json": _json_bytes(lut_json_obj),
        "contract.json": _json_bytes(contract),
        "validation/reference_vectors.json": _json_bytes(vectors),
        "validation/validatePackage.mjs": VALIDATE_PACKAGE_MJS.encode("utf-8"),
        "windy/iceOpticsEvaluator.mjs": REFERENCE_EVALUATOR_MJS.encode("utf-8"),
        "windy/iceOpticsEvaluator.ts": REFERENCE_EVALUATOR_TS.encode("utf-8"),
        "README_WINDY.md": README_WINDY.encode("utf-8"),
    }
    if source_manifest is not None:
        files["source/source_manifest.json"] = _json_bytes(dict(source_manifest))
    status_obj = asdict(lut_status) if lut_status is not None else {
        "loaded": True,
        "path": None,
        "row_count": len(df),
        "spectral_complete": True,
        "state": "ICE_OPTICS_LUT_READY",
        "detail": "",
    }
    manifest = {
        "portable_package_contract_version": PORTABLE_PACKAGE_CONTRACT_VERSION,
        "schema_version": PORTABLE_PACKAGE_SCHEMA_VERSION,
        "ice_optics_contract_version": ICE_OPTICS_CONTRACT_VERSION,
        "evaluator_version": PORTABLE_EVALUATOR_VERSION,
        "physicscore_authoring_version": str(physicscore_version),
        "science_baseline": str(science_baseline),
        "consumer": PORTABLE_CONSUMER,
        "runtime_dependency_on_physicscore": PORTABLE_RUNTIME_DEPENDENCY,
        "runtime_dependency_on_python": "NONE",
        "runtime_dependency_on_streamlit": "NONE",
        "wavelengths_nm": list(ICE_OPTICS_WAVELENGTHS_NM),
        "primary_size_coordinate": PORTABLE_PRIMARY_SIZE_COORDINATE,
        "physics_promotion_allowed": False,
        "lut_status": status_obj,
        "files": {},
    }
    for name, payload in sorted(files.items()):
        manifest["files"][name] = {"byte_size": len(payload), "sha256": _sha(payload)}
    files["manifest.json"] = _json_bytes(manifest)
    return files


def build_portable_package_zip_bytes(
    lut: pd.DataFrame,
    *,
    physicscore_version: str,
    science_baseline: str,
    lut_status: IceOpticsLUTStatus | None = None,
    source_manifest: Mapping[str, Any] | None = None,
) -> bytes:
    files = build_portable_package_files(
        lut,
        physicscore_version=physicscore_version,
        science_baseline=science_baseline,
        lut_status=lut_status,
        source_manifest=source_manifest,
    )
    bio = BytesIO()
    with zipfile.ZipFile(bio, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for name, payload in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, payload)
    return bio.getvalue()


def write_portable_package(
    output_zip: str | Path,
    lut: pd.DataFrame,
    *,
    physicscore_version: str,
    science_baseline: str,
    lut_status: IceOpticsLUTStatus | None = None,
    source_manifest: Mapping[str, Any] | None = None,
) -> Path:
    path = Path(output_zip)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(build_portable_package_zip_bytes(
        lut,
        physicscore_version=physicscore_version,
        science_baseline=science_baseline,
        lut_status=lut_status,
        source_manifest=source_manifest,
    ))
    return path
