from __future__ import annotations

"""Ice-cloud six-band spectral-optics shared contract (Phase 1).

This module remains diagnostic-only through R5.7.41.3.4.10.12.1.
It establishes a calibrated-LUT import contract and a WINDY-facing runtime
export without changing Formation, Viewing, Twilight Glow, or production COT.
The authoritative runtime lookup axis is maximum particle dimension (Dmax).
Source-row-derived effective radius is diagnostic metadata only and is never
used as a cross-band runtime key or silently converted to Dmax.

No ice optical coefficient is fabricated.  A production LUT must be supplied
explicitly (``FIRECLOUD_ICE_OPTICS_LUT`` or a caller-provided DataFrame/path).
The preferred source family is the Yang/Bi/Baum ice-particle scattering
database; the normalizer can derive mass extinction from Qext, projected area,
and particle volume:

    k_ext = Qext * A_proj / (rho_ice * V)

with A in m^2, V in m^3, giving k_ext in m^2 kg^-1.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping
import json
import math
import os

import numpy as np
import pandas as pd

ICE_OPTICS_CONTRACT_VERSION = "FIRECLOUD_ICE_OPTICS_V1"
ICE_OPTICS_PHASE = "PHASE1_DIAGNOSTIC_ONLY_NO_PHYSICS_PROMOTION"
ICE_OPTICS_WAVELENGTHS_NM: tuple[int, ...] = (550, 575, 600, 650, 700, 750)
ICE_DENSITY_KG_M3 = 917.0
DEFAULT_INSTALLED_LUT_PATH = Path.home() / ".cache" / "taiwan_firecloud" / "ice_optics" / "ice_optics_lut_v1.csv"
BUNDLED_CALIBRATED_LUT_PATH = Path(__file__).resolve().parent / "data" / "ice_optics" / "portable_ice_optics_lut_v1.csv"

LUT_REQUIRED_COLUMNS = (
    "wavelength_nm",
    "maximum_dimension_um",
    "effective_diameter_um",
    "effective_radius_um",
    "ice_habit",
    "surface_roughness",
    "mass_extinction_coefficient_m2_kg",
    "single_scattering_albedo",
    "asymmetry_parameter",
    "source_dataset",
    "source_version",
    "source_record_provenance",
)

RUNTIME_BASE_COLUMNS = (
    "time", "solar_altitude_deg", "direction_offset_deg", "distance_km",
    "native_vertical_completeness", "native_iwp_kg_m2",
    "ice_maximum_dimension_um", "ice_effective_radius_um", "ice_habit", "surface_roughness",
    "ice_optics_contract_version", "ice_optics_phase", "ice_optics_state",
    "ice_optics_lookup_state",
    "ice_optics_missing_reason", "ice_optics_lut_source_dataset",
    "ice_optics_lut_source_version", "physics_role",
    "tau_synthesis_allowed", "formation_promotion_allowed",
)


@dataclass(frozen=True)
class IceOpticsLUTStatus:
    loaded: bool
    path: str | None
    row_count: int
    spectral_complete: bool
    state: str
    detail: str = ""


def derive_mass_extinction_coefficient_m2_kg(
    extinction_efficiency: float,
    projected_area_um2: float,
    volume_um3: float,
    ice_density_kg_m3: float = ICE_DENSITY_KG_M3,
) -> float:
    """Convert single-particle Qext/area/volume to mass-extinction coefficient.

    C_ext = Qext * A_proj
    m_ice = rho_ice * V
    k_ext = C_ext / m_ice

    A[um^2] -> m^2 uses 1e-12, V[um^3] -> m^3 uses 1e-18, so the
    unit conversion contributes 1e6.
    """
    q = float(extinction_efficiency)
    a = float(projected_area_um2)
    v = float(volume_um3)
    rho = float(ice_density_kg_m3)
    if not (math.isfinite(q) and math.isfinite(a) and math.isfinite(v) and math.isfinite(rho)):
        return float("nan")
    if q < 0.0 or a <= 0.0 or v <= 0.0 or rho <= 0.0:
        return float("nan")
    return q * (a / v) * 1.0e6 / rho


def geometric_effective_diameter_um(volume_um3: float, projected_area_um2: float) -> float:
    """Return the 1.5*V/A ice-particle effective-diameter coordinate.

    This is retained as a geometry-derived size coordinate.  It must not be
    silently equated with a forecast-model microphysical effective radius.
    """
    v = float(volume_um3)
    a = float(projected_area_um2)
    if not (math.isfinite(v) and math.isfinite(a)) or v <= 0.0 or a <= 0.0:
        return float("nan")
    return 1.5 * v / a


def _normalize_roughness(value: Any) -> str:
    s = str(value).strip()
    return s if s else "UNKNOWN"


def normalize_tamu_isca_frame(
    raw: pd.DataFrame,
    *,
    ice_habit: str,
    surface_roughness: str,
    source_dataset: str = "TAMU_ICE_SINGLE_SCATTERING_V2",
    source_version: str = "Yang2013_Bi2017_V2",
    target_wavelengths_nm: Iterable[int] = ICE_OPTICS_WAVELENGTHS_NM,
) -> pd.DataFrame:
    """Normalize a TAMU ``isca.dat`` table to the Firecloud six-band LUT.

    Expected raw columns (names or positional order): wavelength_um,
    maximum_dimension_um, volume_um3, projected_area_um2,
    extinction_efficiency, single_scattering_albedo, asymmetry_parameter.

    Spectral interpolation is linear *within the calibrated database only* and
    is explicitly recorded in ``source_record_provenance``.  No habit/size
    interpolation is performed here.
    """
    if raw is None or len(raw) == 0:
        return pd.DataFrame(columns=LUT_REQUIRED_COLUMNS)

    names = [
        "wavelength_um", "maximum_dimension_um", "volume_um3",
        "projected_area_um2", "extinction_efficiency",
        "single_scattering_albedo", "asymmetry_parameter",
    ]
    df = raw.copy()
    if not set(names).issubset(df.columns):
        if df.shape[1] < 7:
            raise ValueError("TAMU isca frame requires at least seven columns")
        df = df.iloc[:, :7].copy()
        df.columns = names

    for c in names:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["wavelength_um", "maximum_dimension_um", "volume_um3", "projected_area_um2", "extinction_efficiency"])

    targets = tuple(int(x) for x in target_wavelengths_nm)
    rows: list[dict[str, Any]] = []
    for dmax, g in df.groupby("maximum_dimension_um", sort=True):
        g = g.sort_values("wavelength_um").drop_duplicates("wavelength_um", keep="last")
        x = g["wavelength_um"].to_numpy(dtype=float)
        if len(x) < 2:
            continue
        for wavelength_nm in targets:
            target_um = wavelength_nm / 1000.0
            exact = np.where(np.isclose(x, target_um, rtol=0.0, atol=1e-12))[0]
            if len(exact):
                src = g.iloc[int(exact[0])]
                vals = {c: float(src[c]) for c in names[2:]}
                provenance = "EXACT_SOURCE_WAVELENGTH"
            else:
                hi = int(np.searchsorted(x, target_um, side="right"))
                lo = hi - 1
                if lo < 0 or hi >= len(x):
                    continue
                x0, x1 = float(x[lo]), float(x[hi])
                if not (x0 < target_um < x1):
                    continue
                w = (target_um - x0) / (x1 - x0)
                vals = {}
                for c in names[2:]:
                    y0 = float(g.iloc[lo][c]); y1 = float(g.iloc[hi][c])
                    vals[c] = y0 + w * (y1 - y0)
                provenance = f"LINEAR_WAVELENGTH_INTERPOLATION_WITHIN_SOURCE_GRID:{x0:.6f}-{x1:.6f}um"

            deff = geometric_effective_diameter_um(vals["volume_um3"], vals["projected_area_um2"])
            reff = deff / 2.0 if math.isfinite(deff) else float("nan")
            kext = derive_mass_extinction_coefficient_m2_kg(
                vals["extinction_efficiency"], vals["projected_area_um2"], vals["volume_um3"]
            )
            rows.append({
                "wavelength_nm": int(wavelength_nm),
                "maximum_dimension_um": float(dmax),
                "effective_diameter_um": deff,
                "effective_radius_um": reff,
                "ice_habit": str(ice_habit),
                "surface_roughness": _normalize_roughness(surface_roughness),
                "mass_extinction_coefficient_m2_kg": kext,
                "single_scattering_albedo": float(vals["single_scattering_albedo"]),
                "asymmetry_parameter": float(vals["asymmetry_parameter"]),
                "source_dataset": str(source_dataset),
                "source_version": str(source_version),
                "source_record_provenance": provenance,
            })
    return validate_ice_optics_lut(pd.DataFrame(rows), require_full_six_band=False)


def read_tamu_isca_dat(path: str | os.PathLike[str]) -> pd.DataFrame:
    return pd.read_csv(
        path,
        sep=r"\s+",
        comment="#",
        header=None,
        names=[
            "wavelength_um", "maximum_dimension_um", "volume_um3",
            "projected_area_um2", "extinction_efficiency",
            "single_scattering_albedo", "asymmetry_parameter",
        ],
        engine="python",
    )


def validate_ice_optics_lut(lut: pd.DataFrame, *, require_full_six_band: bool = True) -> pd.DataFrame:
    if lut is None:
        raise ValueError("ice optics LUT is None")
    df = lut.copy()
    missing = set(LUT_REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"ice optics LUT missing columns: {sorted(missing)}")
    if df.empty:
        return df.loc[:, LUT_REQUIRED_COLUMNS].copy()

    numeric = [
        "wavelength_nm", "maximum_dimension_um", "effective_diameter_um",
        "effective_radius_um", "mass_extinction_coefficient_m2_kg",
        "single_scattering_albedo", "asymmetry_parameter",
    ]
    for c in numeric:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    if df[numeric].isna().any().any():
        raise ValueError("ice optics LUT contains nonnumeric/missing optical values")
    if (df["mass_extinction_coefficient_m2_kg"] < 0).any():
        raise ValueError("ice optics LUT contains negative mass extinction coefficient")
    if (~df["single_scattering_albedo"].between(0.0, 1.0)).any():
        raise ValueError("ice optics LUT SSA outside [0,1]")
    if (~df["asymmetry_parameter"].between(-1.0, 1.0)).any():
        raise ValueError("ice optics LUT asymmetry parameter outside [-1,1]")
    allowed = set(ICE_OPTICS_WAVELENGTHS_NM)
    actual = set(df["wavelength_nm"].round().astype(int).unique().tolist())
    if not actual.issubset(allowed):
        raise ValueError(f"ice optics LUT contains non-contract wavelengths: {sorted(actual-allowed)}")
    if require_full_six_band:
        keys = ["ice_habit", "surface_roughness", "maximum_dimension_um"]
        for key, g in df.groupby(keys, dropna=False):
            bands = set(g["wavelength_nm"].round().astype(int).tolist())
            if bands != allowed:
                raise ValueError(f"ice optics LUT incomplete six-band group {key}: {sorted(bands)}")
    return df.loc[:, LUT_REQUIRED_COLUMNS].sort_values(
        ["ice_habit", "surface_roughness", "maximum_dimension_um", "wavelength_nm"]
    ).reset_index(drop=True)


def load_ice_optics_lut(path: str | os.PathLike[str] | None = None) -> tuple[pd.DataFrame, IceOpticsLUTStatus]:
    if path is not None:
        chosen = str(path)
    else:
        chosen = os.getenv("FIRECLOUD_ICE_OPTICS_LUT", "").strip()
        if not chosen and DEFAULT_INSTALLED_LUT_PATH.exists():
            chosen = str(DEFAULT_INSTALLED_LUT_PATH)
    if not chosen:
        return pd.DataFrame(columns=LUT_REQUIRED_COLUMNS), IceOpticsLUTStatus(
            False, str(DEFAULT_INSTALLED_LUT_PATH), 0, False, "ICE_OPTICS_LUT_NOT_CONFIGURED",
            "No calibrated runtime LUT is explicitly configured; bundled certification artifact is not auto-activated.",
        )
    p = Path(chosen).expanduser()
    if not p.exists():
        return pd.DataFrame(columns=LUT_REQUIRED_COLUMNS), IceOpticsLUTStatus(
            False, str(p), 0, False, "ICE_OPTICS_LUT_PATH_NOT_FOUND",
            "Configured LUT path does not exist.",
        )
    try:
        df = pd.read_csv(p)
        df = validate_ice_optics_lut(df, require_full_six_band=True)
    except Exception as exc:
        return pd.DataFrame(columns=LUT_REQUIRED_COLUMNS), IceOpticsLUTStatus(
            False, str(p), 0, False, "ICE_OPTICS_LUT_INVALID", f"{type(exc).__name__}: {exc}",
        )
    return df, IceOpticsLUTStatus(True, str(p), len(df), True, "ICE_OPTICS_LUT_READY")


def _lookup_six_band_by_dmax(
    lut: pd.DataFrame,
    *,
    maximum_dimension_um: float,
    ice_habit: str,
    surface_roughness: str,
) -> tuple[pd.DataFrame, str]:
    """Lookup/interpolate six bands on the authoritative Dmax axis.

    Dmax interpolation is allowed only inside one habit + roughness group.
    Extrapolation, habit interpolation, roughness interpolation, and any
    r_eff->Dmax substitution are prohibited.
    """
    if lut is None or lut.empty:
        return pd.DataFrame(), "ICE_OPTICS_LUT_NOT_LOADED"
    subset = lut[
        lut["ice_habit"].astype(str).eq(str(ice_habit))
        & lut["surface_roughness"].astype(str).eq(str(surface_roughness))
    ].copy()
    if subset.empty:
        return pd.DataFrame(), "ICE_HABIT_ROUGHNESS_NOT_IN_LUT"

    d = float(maximum_dimension_um)
    dims = np.array(
        sorted(pd.to_numeric(subset["maximum_dimension_um"], errors="coerce").dropna().unique()),
        dtype=float,
    )
    if len(dims) == 0 or not math.isfinite(d):
        return pd.DataFrame(), "ICE_MAXIMUM_DIMENSION_MISSING"
    if d < dims.min() - 1e-12 or d > dims.max() + 1e-12:
        return pd.DataFrame(), "ICE_DMAX_OUTSIDE_LUT_DOMAIN"

    exact = np.where(np.isclose(dims, d, rtol=0.0, atol=1e-9))[0]
    if len(exact):
        dd = float(dims[int(exact[0])])
        out = subset[
            np.isclose(
                pd.to_numeric(subset["maximum_dimension_um"], errors="coerce"),
                dd,
                rtol=0.0,
                atol=1e-9,
            )
        ].copy()
        if set(out["wavelength_nm"].round().astype(int)) != set(ICE_OPTICS_WAVELENGTHS_NM):
            return pd.DataFrame(), "ICE_LUT_SIX_BAND_GROUP_INCOMPLETE"
        return out, "EXACT_DMAX_LUT_ROW"

    hi_i = int(np.searchsorted(dims, d, side="right"))
    lo_i = hi_i - 1
    if lo_i < 0 or hi_i >= len(dims):
        return pd.DataFrame(), "ICE_DMAX_OUTSIDE_LUT_DOMAIN"
    d0, d1 = float(dims[lo_i]), float(dims[hi_i])
    g0 = subset[
        np.isclose(
            pd.to_numeric(subset["maximum_dimension_um"], errors="coerce"),
            d0,
            rtol=0.0,
            atol=1e-9,
        )
    ].set_index("wavelength_nm")
    g1 = subset[
        np.isclose(
            pd.to_numeric(subset["maximum_dimension_um"], errors="coerce"),
            d1,
            rtol=0.0,
            atol=1e-9,
        )
    ].set_index("wavelength_nm")
    required = set(ICE_OPTICS_WAVELENGTHS_NM)
    if set(g0.index.astype(int)) != required or set(g1.index.astype(int)) != required:
        return pd.DataFrame(), "ICE_LUT_SIX_BAND_GROUP_INCOMPLETE"

    w = (d - d0) / (d1 - d0)
    rows = []
    for wl in ICE_OPTICS_WAVELENGTHS_NM:
        a = g0.loc[wl]
        b = g1.loc[wl]

        def lerp(col: str) -> float:
            return float(a[col] + w * (b[col] - a[col]))

        rows.append({
            "wavelength_nm": int(wl),
            "maximum_dimension_um": d,
            "effective_diameter_um": lerp("effective_diameter_um"),
            "effective_radius_um": lerp("effective_radius_um"),
            "ice_habit": str(ice_habit),
            "surface_roughness": str(surface_roughness),
            "mass_extinction_coefficient_m2_kg": lerp("mass_extinction_coefficient_m2_kg"),
            "single_scattering_albedo": lerp("single_scattering_albedo"),
            "asymmetry_parameter": lerp("asymmetry_parameter"),
            "source_dataset": str(a["source_dataset"]),
            "source_version": str(a["source_version"]),
            "source_record_provenance": (
                f"LINEAR_DMAX_INTERPOLATION_WITHIN_LUT:{d0:.6f}-{d1:.6f}um"
            ),
        })
    return pd.DataFrame(rows), "LINEAR_DMAX_INTERPOLATION_WITHIN_LUT"

def _native_iwp_kg_m2(row: Mapping[str, Any]) -> float:
    # native_cloud.py stores IWC[g/m3] * dz[km]. Numerically this equals kg/m2:
    # 1 g/m3 * 1 km = 1000 g/m2 = 1 kg/m2.
    v = pd.to_numeric(pd.Series([row.get("ice_water_path_proxy_gm3_km", np.nan)]), errors="coerce").iloc[0]
    return float(v) if pd.notna(v) else float("nan")


def build_ice_cloud_spectral_optics_runtime(
    native_cloud_columns: pd.DataFrame,
    *,
    lut: pd.DataFrame | None = None,
    lut_status: IceOpticsLUTStatus | None = None,
) -> pd.DataFrame:
    """Build diagnostic six-band ice optical depth/transmission rows.

    This remains non-promoting diagnostic output. Positive IWP is evaluated
    only when complete native vertical support, a calibrated Dmax, habit,
    roughness, and a complete authoritative six-band LUT are available.

    ``ice_effective_radius_um`` may be carried through as source/microphysics
    metadata, but it is never used to select a six-band LUT group and is never
    converted to Dmax. Exact-zero IWP remains a physical zero; Missing remains
    Missing.
    """
    cols = list(RUNTIME_BASE_COLUMNS)
    for wl in ICE_OPTICS_WAVELENGTHS_NM:
        cols += [
            f"k_ext_ice_{wl}_m2_kg", f"tau_ice_{wl}", f"ice_transmission_{wl}",
            f"ssa_ice_{wl}", f"g_ice_{wl}",
        ]
    if native_cloud_columns is None or native_cloud_columns.empty:
        return pd.DataFrame(columns=cols)

    if lut is None:
        lut, auto_status = load_ice_optics_lut(None)
        lut_status = lut_status or auto_status
    else:
        lut = validate_ice_optics_lut(lut, require_full_six_band=True)
        lut_status = lut_status or IceOpticsLUTStatus(True, None, len(lut), True, "ICE_OPTICS_LUT_READY")

    rows = []
    for _, src in native_cloud_columns.iterrows():
        rec = {
            k: src.get(k, np.nan)
            for k in [
                "time", "solar_altitude_deg", "direction_offset_deg",
                "distance_km", "native_vertical_completeness",
            ]
        }
        iwp = _native_iwp_kg_m2(src)
        dmax_raw = src.get("ice_maximum_dimension_um", src.get("maximum_dimension_um", np.nan))
        dmax = pd.to_numeric(pd.Series([dmax_raw]), errors="coerce").iloc[0]
        reff = pd.to_numeric(
            pd.Series([src.get("ice_effective_radius_um", np.nan)]), errors="coerce"
        ).iloc[0]
        habit = str(src.get("ice_habit", "")).strip()
        rough = str(
            src.get("ice_surface_roughness", src.get("surface_roughness", ""))
        ).strip()
        completeness = pd.to_numeric(
            pd.Series([src.get("native_vertical_completeness", np.nan)]),
            errors="coerce",
        ).iloc[0]

        rec.update({
            "native_iwp_kg_m2": iwp,
            "ice_maximum_dimension_um": float(dmax) if pd.notna(dmax) else np.nan,
            "ice_effective_radius_um": float(reff) if pd.notna(reff) else np.nan,
            "ice_habit": habit or "UNKNOWN",
            "surface_roughness": rough or "UNKNOWN",
            "ice_optics_contract_version": ICE_OPTICS_CONTRACT_VERSION,
            "ice_optics_phase": ICE_OPTICS_PHASE,
            "ice_optics_lookup_state": "",
            "ice_optics_lut_source_dataset": "",
            "ice_optics_lut_source_version": "",
            "physics_role": "DIAGNOSTIC_ONLY_UNASSIGNED",
            "tau_synthesis_allowed": False,
            "formation_promotion_allowed": False,
        })
        for wl in ICE_OPTICS_WAVELENGTHS_NM:
            rec.update({
                f"k_ext_ice_{wl}_m2_kg": np.nan,
                f"tau_ice_{wl}": np.nan,
                f"ice_transmission_{wl}": np.nan,
                f"ssa_ice_{wl}": np.nan,
                f"g_ice_{wl}": np.nan,
            })

        if pd.isna(iwp):
            rec["ice_optics_state"] = "ICE_IWP_MISSING"
            rec["ice_optics_missing_reason"] = "NATIVE_IWP_MISSING"
        elif pd.isna(completeness) or float(completeness) < 1.0 - 1e-12:
            rec["ice_optics_state"] = "ICE_IWP_INCOMPLETE_NATIVE_VERTICAL_SUPPORT"
            rec["ice_optics_missing_reason"] = "NATIVE_VERTICAL_COMPLETENESS_LT_1"
        elif iwp < 0:
            rec["ice_optics_state"] = "ICE_IWP_INVALID"
            rec["ice_optics_missing_reason"] = "NEGATIVE_IWP"
        elif abs(iwp) <= 1e-15:
            rec["ice_optics_state"] = "NO_ICE_CONDENSATE_AT_NATIVE_STATE"
            rec["ice_optics_missing_reason"] = ""
            for wl in ICE_OPTICS_WAVELENGTHS_NM:
                rec[f"tau_ice_{wl}"] = 0.0
                rec[f"ice_transmission_{wl}"] = 1.0
        elif not lut_status or not lut_status.loaded:
            rec["ice_optics_state"] = "ICE_OPTICS_LUT_UNAVAILABLE"
            rec["ice_optics_missing_reason"] = (
                lut_status.state if lut_status else "ICE_OPTICS_LUT_NOT_LOADED"
            )
        elif pd.isna(dmax):
            rec["ice_optics_state"] = "ICE_MAXIMUM_DIMENSION_MISSING"
            rec["ice_optics_missing_reason"] = "NO_NATIVE_OR_CALIBRATED_ICE_DMAX"
        elif not habit or habit == "UNKNOWN":
            rec["ice_optics_state"] = "ICE_HABIT_MISSING"
            rec["ice_optics_missing_reason"] = "NO_NATIVE_OR_CALIBRATED_ICE_HABIT"
        elif not rough or rough == "UNKNOWN":
            rec["ice_optics_state"] = "ICE_ROUGHNESS_MISSING"
            rec["ice_optics_missing_reason"] = "NO_CALIBRATED_ICE_ROUGHNESS"
        else:
            opt, state = _lookup_six_band_by_dmax(
                lut,
                maximum_dimension_um=float(dmax),
                ice_habit=habit,
                surface_roughness=rough,
            )
            rec["ice_optics_lookup_state"] = state
            if opt.empty:
                rec["ice_optics_state"] = state
                rec["ice_optics_missing_reason"] = state
            else:
                rec["ice_optics_state"] = "ICE_SIX_BAND_OPTICS_READY"
                rec["ice_optics_missing_reason"] = ""
                rec["ice_optics_lut_source_dataset"] = str(opt["source_dataset"].iloc[0])
                rec["ice_optics_lut_source_version"] = str(opt["source_version"].iloc[0])
                for _, o in opt.iterrows():
                    wl = int(o["wavelength_nm"])
                    k = float(o["mass_extinction_coefficient_m2_kg"])
                    tau = float(iwp) * k
                    rec[f"k_ext_ice_{wl}_m2_kg"] = k
                    rec[f"tau_ice_{wl}"] = tau
                    rec[f"ice_transmission_{wl}"] = math.exp(-tau)
                    rec[f"ssa_ice_{wl}"] = float(o["single_scattering_albedo"])
                    rec[f"g_ice_{wl}"] = float(o["asymmetry_parameter"])
        rows.append(rec)
    return pd.DataFrame(rows, columns=cols)

def _distance_band(d: float) -> str:
    if 0 <= d <= 40: return "0-40km_PRIMARY_CANVAS"
    if 40 < d <= 100: return "40-100km_EXTENDED_CANVAS"
    if 100 < d <= 300: return "100-300km_CORRIDOR"
    if 300 < d <= 350: return "300-350km_STRONG_BLOCKING_DIAGNOSTIC"
    if 350 < d <= 440: return "350-440km_REZ_DIAGNOSTIC"
    return "OUTSIDE_0_440km"


def summarize_ice_cloud_spectral_optics(runtime: pd.DataFrame) -> pd.DataFrame:
    base_cols=[
        "time","solar_altitude_deg","distance_band","row_count",
        "ice_zero_iwp_count","ice_positive_iwp_count","optics_ready_count",
        "positive_iwp_optics_complete","ice_optics_state","mean_iwp_kg_m2",
    ]
    spectral_cols=[]
    for wl in ICE_OPTICS_WAVELENGTHS_NM:
        spectral_cols += [f"mean_tau_ice_{wl}", f"max_tau_ice_{wl}"]
    if runtime is None or runtime.empty:
        return pd.DataFrame(columns=base_cols+spectral_cols)
    df=runtime.copy()
    df["distance_band"] = pd.to_numeric(df["distance_km"], errors="coerce").map(lambda x: _distance_band(float(x)) if pd.notna(x) else "UNKNOWN")
    rows=[]
    group_cols=[c for c in ["time","solar_altitude_deg","distance_band"] if c in df.columns]
    for key,g in df.groupby(group_cols, dropna=False, sort=False):
        if not isinstance(key, tuple): key=(key,)
        rec=dict(zip(group_cols,key))
        iwp=pd.to_numeric(g["native_iwp_kg_m2"],errors="coerce")
        positive=iwp > 1e-15
        zero=iwp.notna() & (iwp.abs() <= 1e-15)
        ready=g["ice_optics_state"].astype(str).eq("ICE_SIX_BAND_OPTICS_READY") & positive
        positive_count=int(positive.sum())
        ready_count=int(ready.sum())
        complete=bool(positive_count == ready_count)
        if positive_count == 0:
            band_state="NO_ICE_CONDENSATE_IN_BAND"
        elif complete:
            band_state="ICE_SIX_BAND_OPTICS_READY"
        else:
            band_state="ICE_SIX_BAND_OPTICS_INCOMPLETE"
        rec.update({
            "row_count":int(len(g)),
            "ice_zero_iwp_count":int(zero.sum()),
            "ice_positive_iwp_count":positive_count,
            "optics_ready_count":ready_count,
            "positive_iwp_optics_complete":complete,
            "ice_optics_state":band_state,
            "mean_iwp_kg_m2":float(iwp.mean()) if iwp.notna().any() else np.nan,
        })
        for wl in ICE_OPTICS_WAVELENGTHS_NM:
            if positive_count == 0 and zero.any():
                rec[f"mean_tau_ice_{wl}"]=0.0
                rec[f"max_tau_ice_{wl}"]=0.0
            elif complete and ready_count > 0:
                v=pd.to_numeric(g.loc[ready,f"tau_ice_{wl}"],errors="coerce")
                rec[f"mean_tau_ice_{wl}"]=float(v.mean()) if v.notna().any() else np.nan
                rec[f"max_tau_ice_{wl}"]=float(v.max()) if v.notna().any() else np.nan
            else:
                rec[f"mean_tau_ice_{wl}"]=np.nan
                rec[f"max_tau_ice_{wl}"]=np.nan
        rows.append(rec)
    return pd.DataFrame(rows, columns=base_cols+spectral_cols)


def build_windy_ice_optics_summary(
    summary: pd.DataFrame,
    *,
    physicscore_version: str,
    science_baseline: str,
    lut_status: IceOpticsLUTStatus,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    records=[] if summary is None or summary.empty else summary.to_dict(orient="records")
    base={
        "ice_optics_contract_version": ICE_OPTICS_CONTRACT_VERSION,
        "physicscore_version": str(physicscore_version),
        "science_baseline": str(science_baseline),
        "wavelengths_nm": list(ICE_OPTICS_WAVELENGTHS_NM),
        "primary_size_coordinate": "maximum_dimension_um",
        "phase": ICE_OPTICS_PHASE,
        "physics_promotion_allowed": False,
        "lut": {
            "loaded": bool(lut_status.loaded), "path": lut_status.path,
            "row_count": int(lut_status.row_count), "spectral_complete": bool(lut_status.spectral_complete),
            "state": lut_status.state, "detail": lut_status.detail,
        },
        "records": records,
    }
    frame = summary.copy() if summary is not None else pd.DataFrame()
    if not frame.empty:
        frame.insert(0,"ice_optics_contract_version",ICE_OPTICS_CONTRACT_VERSION)
        frame.insert(1,"physicscore_version",str(physicscore_version))
        frame.insert(2,"science_baseline",str(science_baseline))
        frame.insert(3,"wavelengths_nm","|".join(map(str,ICE_OPTICS_WAVELENGTHS_NM)))
        frame.insert(4,"primary_size_coordinate","maximum_dimension_um")
        frame.insert(5,"physics_promotion_allowed",False)
        frame.insert(6,"lut_state",lut_status.state)
    return frame, base


def ice_optics_contract_payload(*, physicscore_version: str, science_baseline: str) -> dict[str, Any]:
    return {
        "contract_version": ICE_OPTICS_CONTRACT_VERSION,
        "phase": ICE_OPTICS_PHASE,
        "physicscore_version": str(physicscore_version),
        "science_baseline": str(science_baseline),
        "wavelengths_nm": list(ICE_OPTICS_WAVELENGTHS_NM),
        "tau_definition": "tau_ice_lambda = IWP_kg_m2 * k_ext_ice_lambda_m2_kg",
        "transmission_definition": "T_ice_lambda = exp(-tau_ice_lambda)",
        "mass_extinction_definition": "k_ext = Qext * A_proj / (rho_ice * V)",
        "ice_density_kg_m3": ICE_DENSITY_KG_M3,
        "primary_size_coordinate": "maximum_dimension_um",
        "size_interpolation": "LINEAR_DMAX_WITHIN_SAME_HABIT_AND_ROUGHNESS_ONLY; NO_EXTRAPOLATION",
        "iwp_unit_identity": "native ice_water_path_proxy_gm3_km numeric value == kg_m2 only when vertical support is complete",
        "effective_size_note": "1.5*V/A effective diameter/radius is source-row-derived diagnostic mapping metadata only; it is not a runtime key and no r_eff-to-Dmax substitution is permitted.",
        "missing_semantics": "Missing != Clear != Zero; positive IWP requires complete vertical support plus calibrated Dmax/habit/roughness/LUT coverage; no RH/CF/seasonal proxy or r_eff-to-Dmax substitution may synthesize missing optics.",
        "phase1_role": "diagnostic/shared-export only; does not alter Formation, Viewing, Twilight Glow, Red-Light or Photography Decision.",
        "preferred_source_family": {
            "dataset": "Yang/Bi ice particle single-scattering database V2",
            "spectral_range": "0.2-100 um",
            "properties": ["wavelength","maximum dimension","volume","projected area","Qext","SSA","g"],
            "references": ["Yang et al. 2013 JAS DOI 10.1175/JAS-D-12-039.1", "Bi & Yang 2017 JQSRT 189, 228-237"],
        },
    }
