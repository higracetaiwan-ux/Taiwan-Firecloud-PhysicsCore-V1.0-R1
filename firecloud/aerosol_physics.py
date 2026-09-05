from __future__ import annotations
import math
import numpy as np
import pandas as pd

SPECTRAL_SOURCE_WAVELENGTHS_NM = (550, 645, 670, 800)
TARGET_WAVELENGTHS_NM = (600, 650, 700, 750)
DEFAULT_AEROSOL_SCALE_HEIGHT_KM = 2.0


def angstrom_from_pair(aod1: float, wl1_nm: float, aod2: float, wl2_nm: float) -> float:
    """Return Ångström exponent from two positive spectral AODs."""
    vals = (aod1, wl1_nm, aod2, wl2_nm)
    if any(pd.isna(v) for v in vals) or aod1 <= 0 or aod2 <= 0 or wl1_nm <= 0 or wl2_nm <= 0 or wl1_nm == wl2_nm:
        return np.nan
    return -math.log(float(aod1) / float(aod2)) / math.log(float(wl1_nm) / float(wl2_nm))


def spectral_aod_loglog_interpolate(wavelength_nm: float, known: dict[int, float]) -> float:
    """Log-log interpolate/extrapolate AOD using nearest valid spectral points.

    This preserves the local power-law behaviour rather than imposing a fixed
    global Ångström exponent. At least two valid positive AOD wavelengths are required.
    """
    pts = sorted((float(w), float(v)) for w, v in known.items() if pd.notna(v) and float(v) > 0 and float(w) > 0)
    if len(pts) < 2:
        return np.nan
    x = math.log(float(wavelength_nm))
    # bracket if possible, otherwise use nearest end pair for local extrapolation
    pair = None
    for a, b in zip(pts[:-1], pts[1:]):
        if a[0] <= wavelength_nm <= b[0]:
            pair = (a, b); break
    if pair is None:
        pair = (pts[0], pts[1]) if wavelength_nm < pts[0][0] else (pts[-2], pts[-1])
    (w1, a1), (w2, a2) = pair
    y1, y2 = math.log(a1), math.log(a2)
    y = y1 + (x - math.log(w1)) * (y2 - y1) / (math.log(w2) - math.log(w1))
    return math.exp(y)


def normalized_exponential_vertical_fraction(z0_km: float, z1_km: float, scale_height_km: float = DEFAULT_AEROSOL_SCALE_HEIGHT_KM) -> float:
    """Fraction of a normalized exponential aerosol column in altitude slab z0..z1.

    Integral of exp(-z/H)/H from z0 to z1. This is an explicit engineering
    vertical-profile assumption used only when a native 3-D aerosol extinction
    profile is unavailable.
    """
    H = max(0.05, float(scale_height_km))
    lo, hi = sorted((max(0.0, float(z0_km)), max(0.0, float(z1_km))))
    return max(0.0, math.exp(-lo/H) - math.exp(-hi/H))


def ray_segment_aerosol_tau(column_aod: float, z0_km: float, z1_km: float, horizontal_km: float,
                             scale_height_km: float = DEFAULT_AEROSOL_SCALE_HEIGHT_KM) -> float:
    """Approximate aerosol optical depth along one 3-D ray segment.

    The local column AOD is converted to a normalized exponential extinction
    profile. We do NOT add total-column AODs from successive route points.
    Instead, each segment uses the extinction represented by the altitude interval
    actually traversed by that segment and scales by segment/slab vertical length.
    Near-horizontal segments are handled with the midpoint extinction coefficient.
    """
    if pd.isna(column_aod) or float(column_aod) < 0:
        return np.nan
    H = max(0.05, float(scale_height_km))
    dz = abs(float(z1_km) - float(z0_km))
    ds = math.hypot(float(horizontal_km), dz)
    if ds <= 0:
        return 0.0
    if dz > 1e-6:
        frac = normalized_exponential_vertical_fraction(z0_km, z1_km, H)
        return float(column_aod) * frac * ds / dz
    zmid = max(0.0, 0.5 * (float(z0_km) + float(z1_km)))
    beta_per_km = float(column_aod) * math.exp(-zmid/H) / H
    return beta_per_km * ds


def derive_route_spectral_aod(snapshot: pd.DataFrame, targets=TARGET_WAVELENGTHS_NM) -> pd.DataFrame:
    """Attach local spectral AOD and local Ångström diagnostics to route rows.

    Expected real provider columns are aod550/aod645/aod670/aod800. If fewer than
    two valid spectral wavelengths exist, target spectral AOD stays Missing.
    """
    if snapshot is None or snapshot.empty:
        return pd.DataFrame()
    out = snapshot.copy()
    src_cols = {wl: f"aod{wl}" for wl in SPECTRAL_SOURCE_WAVELENGTHS_NM}
    def calc(row, wl):
        known = {w: row.get(c, np.nan) for w, c in src_cols.items()}
        return spectral_aod_loglog_interpolate(wl, known)
    for wl in targets:
        out[f"aod{wl}"] = out.apply(lambda r: calc(r, wl), axis=1)
    out["angstrom_550_800"] = out.apply(lambda r: angstrom_from_pair(r.get("aod550", np.nan), 550, r.get("aod800", np.nan), 800), axis=1)
    valid_count = out[[c for c in src_cols.values() if c in out.columns]].notna().sum(axis=1) if any(c in out.columns for c in src_cols.values()) else 0
    out["spectral_aod_quality"] = np.where(np.asarray(valid_count) >= 2, "REAL_MULTI_WAVELENGTH_COLUMN_AOD", "SPECTRAL_AOD_MISSING")
    return out


def integrate_route_aerosol_to_targets(voxels: pd.DataFrame, route_spectral: pd.DataFrame,
                                        target_wavelengths=TARGET_WAVELENGTHS_NM,
                                        scale_height_km: float = DEFAULT_AEROSOL_SCALE_HEIGHT_KM) -> pd.DataFrame:
    """Integrate fallback aerosol tau with pre-indexed route arrays.

    V8.4.0.2 performance fix: the old implementation repeatedly filtered a Pandas
    DataFrame inside every voxel × segment × wavelength loop. On the full
    3×23×36 lattice this could dominate a whole checkpoint. Route data are now
    indexed once per direction/wavelength and NumPy interpolation is used inside
    the compact numeric loop. Physics and Missing semantics are unchanged.
    """
    if voxels is None or voxels.empty:
        return pd.DataFrame()
    out = voxels.copy()
    if route_spectral is None or route_spectral.empty:
        for wl in target_wavelengths:
            out[f"route_aerosol_tau_{wl}nm"] = np.nan
            out[f"route_aerosol_transmission_{wl}nm"] = np.nan
        out["aerosol_path_quality"] = "AEROSOL_ROUTE_MISSING"
        return out
    alt_col = "voxel_center_km" if "voxel_center_km" in out.columns else ("altitude_km" if "altitude_km" in out.columns else None)
    if alt_col is None:
        for wl in target_wavelengths:
            out[f"route_aerosol_tau_{wl}nm"] = np.nan
            out[f"route_aerosol_transmission_{wl}nm"] = np.nan
        out["aerosol_path_quality"] = "VOXEL_ALTITUDE_MISSING"
        return out

    route = route_spectral.copy()
    route["distance_km"] = pd.to_numeric(route["distance_km"], errors="coerce")
    route["direction_offset_deg"] = pd.to_numeric(route["direction_offset_deg"], errors="coerce")
    index = {}
    for off, g in route.groupby("direction_offset_deg", sort=False):
        g = g.sort_values("distance_km")
        base_d = g["distance_km"].to_numpy(dtype=float)
        spec = {}
        for wl in target_wavelengths:
            col = f"aod{wl}"
            if col not in g.columns:
                spec[wl] = (np.array([], dtype=float), np.array([], dtype=float))
                continue
            vals = pd.to_numeric(g[col], errors="coerce").to_numpy(dtype=float)
            m = np.isfinite(base_d) & np.isfinite(vals)
            spec[wl] = (base_d[m], vals[m])
        index[float(off)] = (base_d[np.isfinite(base_d)], spec)

    results = {wl: np.full(len(out), np.nan, dtype=float) for wl in target_wavelengths}
    qualities = np.empty(len(out), dtype=object)
    offs = pd.to_numeric(out.get("direction_offset_deg", 0.0), errors="coerce").to_numpy(dtype=float)
    dists = pd.to_numeric(out.get("distance_km", 0.0), errors="coerce").to_numpy(dtype=float)
    alts = pd.to_numeric(out[alt_col], errors="coerce").to_numpy(dtype=float)
    H = max(1e-6, float(scale_height_km))

    for i, (off, target_d, target_z) in enumerate(zip(offs, dists, alts)):
        if not np.isfinite(target_d) or not np.isfinite(target_z) or off not in index:
            qualities[i] = "AEROSOL_ROUTE_MISSING"; continue
        if target_d <= 0:
            for wl in target_wavelengths: results[wl][i] = 0.0
            qualities[i] = "ZERO_PATH"; continue
        base_d, spec = index[off]
        ds = base_d[(base_d >= 0.0) & (base_d <= target_d)]
        ds_grid = np.unique(np.concatenate(([0.0], ds, [target_d])))
        if ds_grid.size < 2:
            qualities[i] = "AEROSOL_ROUTE_MISSING"; continue
        tau = {wl: 0.0 for wl in target_wavelengths}; ok_all = True
        for d0, d1 in zip(ds_grid[:-1], ds_grid[1:]):
            if d1 <= d0: continue
            z0 = target_z * d0 / target_d; z1 = target_z * d1 / target_d
            dmid = 0.5 * (d0 + d1)
            dz = z1 - z0
            seg_len_km = math.hypot(d1 - d0, dz)
            zmid = 0.5 * (z0 + z1)
            vertical_shape = math.exp(-max(0.0, zmid) / H) / H
            for wl in target_wavelengths:
                xd, xv = spec[wl]
                if xd.size == 0:
                    tau[wl] = np.nan; ok_all = False; continue
                aod = float(np.interp(dmid, xd, xv))
                if np.isnan(tau[wl]): continue
                tau[wl] += max(0.0, aod) * vertical_shape * seg_len_km
        for wl in target_wavelengths: results[wl][i] = tau[wl]
        qualities[i] = "COLUMN_AOD_TO_EXPONENTIAL_3D_PROFILE" if ok_all else "SPECTRAL_AOD_INCOMPLETE"

    for wl in target_wavelengths:
        out[f"route_aerosol_tau_{wl}nm"] = results[wl]
        out[f"route_aerosol_transmission_{wl}nm"] = np.exp(-results[wl])
    out["aerosol_vertical_profile_scale_height_km"] = float(scale_height_km)
    out["aerosol_path_quality"] = qualities
    return out

def _cams_profile_at_row(row: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    """Return altitude-km and native CAMS 532-nm extinction profile from one route row."""
    zs=[]; bs=[]
    for c in row.index:
        if not str(c).startswith("cams_aerext532_m1_") or not str(c).endswith("hPa"):
            continue
        try:
            p=int(str(c).split("_")[-1].replace("hPa",""))
        except Exception:
            continue
        b=row.get(c,np.nan); z=row.get(f"cams_geopotential_height_m_{p}hPa",np.nan)
        if pd.notna(b) and pd.notna(z):
            zs.append(float(z)/1000.0); bs.append(max(0.0,float(b)))
    if len(zs)<2:
        return np.array([],dtype=float),np.array([],dtype=float)
    order=np.argsort(zs)
    return np.asarray(zs,dtype=float)[order],np.asarray(bs,dtype=float)[order]


def _spectral_scale_from_native_row(row: pd.Series, wavelength_nm: int) -> float:
    known={wl:row.get(f"aod{wl}",np.nan) for wl in SPECTRAL_SOURCE_WAVELENGTHS_NM}
    a532=spectral_aod_loglog_interpolate(532,known)
    at=spectral_aod_loglog_interpolate(float(wavelength_nm),known)
    if pd.isna(a532) or pd.isna(at) or a532<=0:
        return np.nan
    return float(at)/float(a532)


def integrate_native_cams_aerosol_sun_to_targets(
    voxels: pd.DataFrame,
    cams_snapshot: pd.DataFrame,
    solar_altitude_deg: float,
    ray_altitude_func,
    earth_radius_km: float = 6371.0,
    target_wavelengths=TARGET_WAVELENGTHS_NM,
    atmosphere_top_km: float = 30.0,
) -> pd.DataFrame:
    """Integrate native CAMS aerosol extinction on incoming Sun→Canvas rays.

    V8.4.0.2 pre-indexes each CAMS route point's vertical profile and spectral
    scaling once. The previous code rebuilt those arrays for every target voxel,
    which made the first checkpoint appear to hang. Scientific definitions and
    fail-closed semantics are unchanged.
    """
    if voxels is None or voxels.empty:
        return pd.DataFrame()
    out = voxels.copy()
    for wl in target_wavelengths:
        out[f"native_cams_aerosol_tau_{wl}nm"] = np.nan
        out[f"native_cams_aerosol_transmission_{wl}nm"] = np.nan
    out["native_cams_aerosol_path_completeness"] = 0.0
    out["native_cams_aerosol_domain_complete"] = False
    out["native_cams_aerosol_quality"] = "CAMS_NATIVE_3D_AEROSOL_MISSING"
    if cams_snapshot is None or cams_snapshot.empty:
        return out
    alt_col = "voxel_center_km" if "voxel_center_km" in out.columns else ("altitude_km" if "altitude_km" in out.columns else None)
    if alt_col is None:
        out["native_cams_aerosol_quality"] = "VOXEL_ALTITUDE_MISSING"; return out

    route = cams_snapshot.copy()
    route["distance_km"] = pd.to_numeric(route["distance_km"], errors="coerce")
    route["direction_offset_deg"] = pd.to_numeric(route["direction_offset_deg"], errors="coerce")
    route_index = {}
    for off, g in route.groupby("direction_offset_deg", sort=False):
        entries = []
        for _, r in g.sort_values("distance_km").iterrows():
            d = r.get("distance_km", np.nan)
            if pd.isna(d): continue
            zs, bs = _cams_profile_at_row(r)
            scales = np.asarray([_spectral_scale_from_native_row(r, wl) for wl in target_wavelengths], dtype=float)
            entries.append((float(d), zs, bs, scales))
        route_index[float(off)] = entries

    n = len(out)
    tau_arr = {wl: np.full(n, np.nan, dtype=float) for wl in target_wavelengths}
    comp_arr = np.zeros(n, dtype=float); dom_arr = np.zeros(n, dtype=bool); qual_arr = np.empty(n, dtype=object)
    offs = pd.to_numeric(out.get("direction_offset_deg", 0.0), errors="coerce").to_numpy(dtype=float)
    dts = pd.to_numeric(out.get("distance_km", 0.0), errors="coerce").to_numpy(dtype=float)
    zts = pd.to_numeric(out[alt_col], errors="coerce").to_numpy(dtype=float)

    for i, (off, d_t, z_t) in enumerate(zip(offs, dts, zts)):
        entries = route_index.get(off, ())
        tau = np.zeros(len(target_wavelengths), dtype=float); known_len = total_len = 0.0
        final_ray_h = z_t; any_spectral = False; prev_d = d_t
        for d_s, zs, bs, scales in entries:
            if d_s <= d_t + 1e-9 or d_s <= prev_d + 1e-9: continue
            mid = 0.5 * (prev_d + d_s)
            ray_h = ray_altitude_func(d_t, z_t, mid, float(solar_altitude_deg), float(earth_radius_km))
            if ray_h is None or ray_h < 0:
                prev_d = d_s; continue
            final_ray_h = float(ray_h)
            if ray_h >= atmosphere_top_km: break
            next_h = ray_altitude_func(d_t, z_t, d_s, float(solar_altitude_deg), float(earth_radius_km))
            dz = 0.0 if next_h is None else float(next_h) - float(ray_h)
            seg_m = math.hypot(float(d_s - prev_d), dz) * 1000.0
            total_len += seg_m
            if zs.size < 2 or ray_h < zs[0] or ray_h > zs[-1] or not np.all(np.isfinite(scales)):
                prev_d = d_s; continue
            beta532 = float(np.interp(float(ray_h), zs, bs))
            any_spectral = True; known_len += seg_m
            tau += max(0.0, beta532) * scales * seg_m
            prev_d = d_s
        comp_arr[i] = known_len / total_len if total_len > 0 else 0.0
        dom_arr[i] = bool(final_ray_h >= atmosphere_top_km)
        quality = ("CAMS_NATIVE_3D_EXT532+REAL_SPECTRAL_AOD_SUN_TO_CANVAS" if any_spectral and known_len > 0 else
                   "CAMS_NATIVE_EXT532_PRESENT_SPECTRAL_AOD_OR_VERTICAL_SUPPORT_MISSING")
        if any_spectral and known_len > 0 and not dom_arr[i]: quality += ";ROUTE_DOMAIN_TRUNCATED"
        qual_arr[i] = quality
        if any_spectral and known_len > 0:
            for j, wl in enumerate(target_wavelengths): tau_arr[wl][i] = tau[j]

    for wl in target_wavelengths:
        out[f"native_cams_aerosol_tau_{wl}nm"] = tau_arr[wl]
        out[f"native_cams_aerosol_transmission_{wl}nm"] = np.exp(-tau_arr[wl])
    out["native_cams_aerosol_path_completeness"] = comp_arr
    out["native_cams_aerosol_domain_complete"] = dom_arr
    out["native_cams_aerosol_quality"] = qual_arr
    return out

