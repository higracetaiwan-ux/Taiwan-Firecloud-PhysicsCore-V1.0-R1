from __future__ import annotations
import math
import numpy as np
import pandas as pd
from .aerosol_physics import (
    derive_route_spectral_aod, integrate_route_aerosol_to_targets,
    integrate_native_cams_aerosol_sun_to_targets,
)
from .geometry import ray_altitude_km_at_surface_distance
from .gas_rt import integrate_gas_sun_to_targets, active_gas_wavelengths, _local_band_coefficients_from_csv, GasRTPreparedContext
from .contracts import SIX_BAND_WAVELENGTHS_NM

SPECTRAL_WAVELENGTHS_NM = (600, 650, 700, 750)
DEFAULT_ANGSTROM_DIAGNOSTIC = 1.30  # only used when spectral AOD is not available; explicitly labelled


def rayleigh_vertical_optical_depth(wavelength_nm: float, pressure_hpa: float = 1013.25) -> float:
    """Bodhaine-style visible Rayleigh optical-depth approximation.

    lambda is in micrometres. Pressure scaling is explicit. This is a compact
    broadband implementation for V8.3 diagnostics, not line-by-line RT.
    """
    lam = max(0.2, float(wavelength_nm) / 1000.0)
    inv2 = lam ** -2
    tau = 0.008569 * lam ** -4 * (1.0 + 0.0113 * inv2 + 0.00013 * inv2 * inv2)
    return max(0.0, tau * max(0.0, float(pressure_hpa)) / 1013.25)


def aerosol_optical_depth(wavelength_nm: float, aod550: float, angstrom_exponent: float) -> float:
    if pd.isna(aod550) or pd.isna(angstrom_exponent):
        return np.nan
    return max(0.0, float(aod550)) * (float(wavelength_nm) / 550.0) ** (-float(angstrom_exponent))


def twilight_slant_factor(solar_altitude_deg: float, cap: float = 40.0) -> float:
    """Finite diagnostic air-mass factor for long twilight paths.

    Plane-parallel secant diverges at 0 deg and is not appropriate for the
    spherical twilight path. Until curved-atmosphere integration is installed,
    V8.3 uses an explicitly labelled capped engineering air-mass factor.
    """
    depression = abs(float(solar_altitude_deg))
    # Kasten-like finite near-horizon approximation evaluated on depression angle.
    elev = max(0.01, depression)
    m = 1.0 / (math.sin(math.radians(elev)) + 0.50572 * (elev + 6.07995) ** -1.6364)
    return min(float(cap), max(1.0, m))


def gas_band_optical_depth(wavelength_nm: float, *, ozone_du: float | None = None,
                           precipitable_water_mm: float | None = None) -> tuple[float, str]:
    """Gas-absorption interface for 600-750 nm.

    V8.3 deliberately does not invent O3/O2/H2O line absorption. Without a
    HITRAN/MT_CKD coefficient table and atmospheric columns, gas tau is Missing.
    This preserves the spectral RT architecture without turning placeholders into
    physical measurements.
    """
    return np.nan, "HITRAN_BAND_COEFFICIENTS_NOT_CONNECTED"


def build_spectral_rt(native_optical_voxels: pd.DataFrame, solar_altitude_deg: float,
                      aerosol_snapshot: pd.DataFrame | None = None,
                      cams_native_aerosol_snapshot: pd.DataFrame | None = None,
                      angstrom_exponent: float | None = None,
                      pressure_hpa: float = 1013.25, earth_radius_km: float = 6371.0,
                      gas_profile: pd.DataFrame | None = None, progress_callback=None,
                      prepared_route_spectral_aod: pd.DataFrame | None = None,
                      gas_prepared_context: GasRTPreparedContext | None = None) -> pd.DataFrame:
    """Attach 600-750 nm spectral RT with route-resolved aerosol path physics.

    V8.3.2 no longer multiplies one total-column AOD by a generic twilight air-mass
    factor for the aerosol term. When real multi-wavelength column AOD is present
    (aod550/aod645/aod670/aod800), it is locally interpolated to the active diagnostic bands
    and reconstructed into an explicit normalized vertical extinction profile; the
    3-D observer-to-target ray is then integrated segment by segment.

    If only AOD550 is available, spectral aerosol transmission remains Missing.
    No fixed Ångström exponent is silently introduced.
    """
    if native_optical_voxels.empty:
        return pd.DataFrame()
    # V1.0 R3 preserves the frozen six-band contract even when a gas
    # coefficient is unavailable for one band (notably 550 nm); that component
    # remains Missing rather than dropping the wavelength from the result.
    wavelengths=tuple(SIX_BAND_WAVELENGTHS_NM)
    def _emit(frac: float, message: str):
        if progress_callback is not None:
            try: progress_callback(float(frac), str(message))
            except Exception: pass
    _emit(0.02, "準備 550–750 nm 六波段光譜狀態")
    out = native_optical_voxels.copy()
    m = twilight_slant_factor(solar_altitude_deg)
    cloud_tau = pd.to_numeric(out.get("slant_cloud_optical_depth_estimate", np.nan), errors="coerce")
    cloud_t = np.exp(-cloud_tau)
    out["spectral_airmass_factor"] = m  # retained for Rayleigh diagnostic only

    if prepared_route_spectral_aod is not None:
        route = prepared_route_spectral_aod.copy()
    else:
        route = derive_route_spectral_aod(aerosol_snapshot, targets=wavelengths) if aerosol_snapshot is not None and not aerosol_snapshot.empty else pd.DataFrame()
    _emit(0.12, "建立路徑光譜 AOD 狀態")
    if not route.empty and "point_id" in out.columns:
        attach_cols=[c for c in ["point_id","aod550","aod645","aod670","aod800","angstrom_550_800","spectral_aod_quality","aerosol_provider"] if c in route.columns]
        if attach_cols:
            out=out.merge(route[attach_cols].drop_duplicates("point_id"), on="point_id", how="left")
    else:
        out["aod550"]=np.nan
        out["aerosol_provider"]="UNAVAILABLE"

    # V8.3.3 prefers native CAMS 3-D extinction on the physically relevant incoming
    # Sun→Canvas path. V8.3.2 column-AOD/exponential-profile integration is retained
    # only as a separately labelled fallback when native CAMS 3-D is unavailable.
    _emit(0.18, "積分 CAMS 3D 氣膠 Sun→Canvas 光路")
    native_cams = integrate_native_cams_aerosol_sun_to_targets(
        out, cams_native_aerosol_snapshot, solar_altitude_deg,
        ray_altitude_km_at_surface_distance, earth_radius_km=earth_radius_km,
        target_wavelengths=wavelengths,
    ) if cams_native_aerosol_snapshot is not None and not cams_native_aerosol_snapshot.empty else pd.DataFrame()
    if not native_cams.empty:
        native_cols=[c for c in native_cams.columns if c.startswith("native_cams_aerosol_")]
        for c in native_cols:
            out[c]=native_cams[c].to_numpy()
    _emit(0.38, "檢查光譜 AOD 備援需求")
    # V8.4.11.1: the previous code always integrated the exponential-profile
    # fallback for all 6480 voxels even when native CAMS 3-D aerosol already
    # covered every direct-solar target. Compute that fallback only where it may
    # actually be needed; no optical value is changed when native data are full.
    native650=pd.to_numeric(out.get("native_cams_aerosol_tau_650nm",pd.Series(np.nan,index=out.index)),errors="coerce")
    applicable=pd.to_numeric(out.get("geometric_illuminated_fraction",pd.Series(1.0,index=out.index)),errors="coerce").fillna(0.0)>0.0
    need_fallback=bool((applicable & native650.isna()).any())
    if need_fallback and not route.empty:
        _emit(0.43, "積分多波段 AOD 備援光路")
        out = integrate_route_aerosol_to_targets(out, route, target_wavelengths=wavelengths)
    else:
        for wl in wavelengths:
            out[f"route_aerosol_tau_{wl}nm"]=np.nan
            out[f"route_aerosol_transmission_{wl}nm"]=np.nan
        out["route_aerosol_path_completeness"]=1.0 if not need_fallback else 0.0
        out["route_aerosol_quality"]="FALLBACK_NOT_REQUIRED_NATIVE_CAMS_COMPLETE" if not need_fallback else "FALLBACK_UNAVAILABLE"
    out["spectral_aod550_source"] = out.get("aerosol_provider", "UNAVAILABLE")
    out["spectral_angstrom_exponent"] = pd.to_numeric(out.get("angstrom_550_800", np.nan), errors="coerce")
    native_series = out["native_cams_aerosol_tau_650nm"] if "native_cams_aerosol_tau_650nm" in out.columns else pd.Series(np.nan, index=out.index)
    native_ok = pd.to_numeric(native_series, errors="coerce").notna()
    fallback_ok = pd.to_numeric(out.get("route_aerosol_tau_650nm", np.nan), errors="coerce").notna()
    out["spectral_rt_quality"] = np.select(
        [native_ok, fallback_ok],
        ["RAYLEIGH+CAMS_NATIVE_3D_AEROSOL_SUN_TO_CANVAS+CLOUD_NATIVE;GAS_MISSING",
         "RAYLEIGH+REAL_MULTI_WAVELENGTH_AOD+EXPONENTIAL_PROFILE_FALLBACK+CLOUD_NATIVE;GAS_MISSING"],
        default="RAYLEIGH+CLOUD_NATIVE;SPECTRAL_AEROSOL_MISSING;ANGSTROM_MISSING;GAS_MISSING",
    )

    _emit(0.55, "開始 HITRAN/CAMS O₃ 氣體光路積分")
    def _gas_progress(frac, message):
        _emit(0.55 + 0.35*max(0.0,min(1.0,float(frac))), message)
    gas_out = integrate_gas_sun_to_targets(
        out, gas_profile if gas_profile is not None else pd.DataFrame(), solar_altitude_deg,
        earth_radius_km=earth_radius_km, progress_callback=_gas_progress,
        prepared_context=gas_prepared_context,
    )
    _emit(0.92, "合成 Rayleigh／氣膠／氣體／雲光學")
    for c in [c for c in gas_out.columns if c.startswith("gas_tau_") or c.startswith("gas_transmission_") or c.startswith("o3_transmission_") or c in ("gas_rt_quality","gas_path_completeness","gas_rt_failure_cause","gas_rt_domain_status","gas_rt_expected_termination","gas_profile_top_km","gas_rt_boundary_clipped","rt_applicable_direct_solar")]:
        out[c] = gas_out[c].to_numpy()

    # V8.4.6.3: refresh composite quality after gas integration; older versions
    # retained the initial GAS_MISSING label even when Hybrid gas RT succeeded.
    gas_domain = out.get("gas_rt_domain_status", pd.Series("", index=out.index)).astype(str)
    gas_ok = (
        out.get("gas_rt_quality", pd.Series("", index=out.index)).astype(str).str.startswith("HITRAN_DERIVED_3D_GAS_RT")
        & ~gas_domain.str.startswith("TRUE_")
    )
    base_q = out["spectral_rt_quality"].astype(str).str.replace(";GAS_MISSING", "", regex=False)
    out["spectral_rt_quality"] = np.where(gas_ok, base_q + ";GAS_RT_AVAILABLE", base_q + ";GAS_MISSING")
    gas_failure = out.get("gas_rt_failure_cause", pd.Series("", index=out.index)).fillna("").astype(str)
    aerosol_missing = (~native_ok) & (~fallback_ok)
    out["spectral_rt_missing_cause"] = np.select(
        [gas_failure.ne(""), aerosol_missing],
        ["GAS_" + gas_failure, "AEROSOL_SPECTRAL_PATH_MISSING"],
        default="",
    )
    clipped = out.get("gas_rt_boundary_clipped", pd.Series(False, index=out.index)).fillna(False).astype(bool)
    out["spectral_rt_boundary_clipped"] = clipped
    out["spectral_rt_quality"] = np.where(
        clipped & gas_ok,
        out["spectral_rt_quality"].astype(str) + ";GAS_PROFILE_BOUNDARY_CLIPPED",
        out["spectral_rt_quality"],
    )

    # R5.6.1: build six-band diagnostic columns in one batch. Repeated
    # DataFrame.insert/setitem operations fragmented the frame and generated
    # large pandas PerformanceWarnings in every angle. This changes storage
    # mechanics only; equations and band values are unchanged.
    band_cols = {}
    geom=pd.to_numeric(out.get("geometric_illuminated_fraction",np.nan),errors="coerce")
    cf=pd.to_numeric(out.get("cloud_fraction_used",out.get("cloud_fraction",np.nan)),errors="coerce")
    gas_quality = out.get("gas_rt_quality", pd.Series("HITRAN_GAS_MISSING", index=out.index))
    for wl in wavelengths:
        tau_r = rayleigh_vertical_optical_depth(wl, pressure_hpa) * m
        t_r = math.exp(-tau_r)
        native_tau = pd.to_numeric(out[f"native_cams_aerosol_tau_{wl}nm"] if f"native_cams_aerosol_tau_{wl}nm" in out.columns else pd.Series(np.nan,index=out.index), errors="coerce")
        native_t = pd.to_numeric(out[f"native_cams_aerosol_transmission_{wl}nm"] if f"native_cams_aerosol_transmission_{wl}nm" in out.columns else pd.Series(np.nan,index=out.index), errors="coerce")
        route_tau = native_tau.where(native_tau.notna(), pd.to_numeric(out.get(f"route_aerosol_tau_{wl}nm", np.nan), errors="coerce"))
        route_t = native_t.where(native_t.notna(), pd.to_numeric(out.get(f"route_aerosol_transmission_{wl}nm", np.nan), errors="coerce"))
        if angstrom_exponent is not None:
            aod550_series = pd.to_numeric(out.get("aod550", np.nan), errors="coerce")
            legacy_tau = aod550_series.map(lambda x: aerosol_optical_depth(wl, x, angstrom_exponent) if pd.notna(x) else np.nan) * m
            route_tau = route_tau.where(route_tau.notna(), legacy_tau)
            route_t = route_t.where(route_t.notna(), np.exp(-legacy_tau))
        gas_t = pd.to_numeric(out.get(f"gas_transmission_{wl}nm", np.nan), errors="coerce")
        partial = cloud_t * t_r * route_t
        band_cols[f"rayleigh_tau_{wl}nm"] = np.full(len(out), tau_r)
        band_cols[f"rayleigh_transmission_{wl}nm"] = np.full(len(out), t_r)
        band_cols[f"aerosol_tau_{wl}nm"] = route_tau.to_numpy() if hasattr(route_tau, "to_numpy") else route_tau
        band_cols[f"aerosol_transmission_{wl}nm"] = route_t.to_numpy() if hasattr(route_t, "to_numpy") else route_t
        band_cols[f"gas_status_{wl}nm"] = np.asarray(gas_quality)
        band_cols[f"cloud_transmission_{wl}nm"] = np.full(len(out), cloud_t) if np.isscalar(cloud_t) else np.asarray(cloud_t)
        band_cols[f"partial_spectral_transmission_{wl}nm"] = np.asarray(partial)
        band_cols[f"full_spectral_transmission_{wl}nm"] = np.asarray(partial * gas_t)
        band_cols[f"canvas_partial_spectral_illumination_{wl}nm"] = np.asarray(geom * cf * partial)
    # Drop any pre-existing same-name columns so concat remains deterministic.
    if band_cols:
        out = out.drop(columns=[c for c in band_cols if c in out.columns], errors="ignore")
        out = pd.concat([out, pd.DataFrame(band_cols, index=out.index)], axis=1)
    _emit(1.0, f"{wavelengths[0]}–{wavelengths[-1]} nm 光譜 RT 完成")
    return out


def summarize_spectral_rt(spectral_voxels: pd.DataFrame) -> pd.DataFrame:
    if spectral_voxels.empty:
        return pd.DataFrame()
    rows=[]
    detected=[]
    for c in spectral_voxels.columns:
        if c.startswith("full_spectral_transmission_") and c.endswith("nm"):
            try: detected.append(int(c.rsplit("_",1)[1][:-2]))
            except ValueError: pass
    wavelengths=tuple(sorted(set(detected))) or SPECTRAL_WAVELENGTHS_NM
    keys=["solar_altitude_deg","direction_offset_deg","distance_km"]
    for key,g in spectral_voxels.groupby(keys, dropna=False, sort=False):
        rec=dict(zip(keys,key))
        rec["band"] = g["band"].iloc[0] if "band" in g else ""
        for wl in wavelengths:
            for prefix in ("partial_spectral_transmission", "canvas_partial_spectral_illumination"):
                c=f"{prefix}_{wl}nm"
                rec[f"mean_{c}"]=float(g[c].mean(skipna=True)) if c in g and g[c].notna().any() else np.nan
        full_cols=[f"full_spectral_transmission_{wl}nm" for wl in wavelengths]
        rec["spectral_rt_quality"]="FULL_RT" if all(c in g and g[c].notna().any() for c in full_cols) else "PARTIAL_RT_GAS_MISSING"
        rows.append(rec)
    return pd.DataFrame(rows)
