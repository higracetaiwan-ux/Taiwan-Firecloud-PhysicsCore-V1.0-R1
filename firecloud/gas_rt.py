from __future__ import annotations
import math, os
from functools import lru_cache
from dataclasses import dataclass
import numpy as np
from .shared_geometry.ray import ray_altitude_matrix_km
import pandas as pd

GAS_WAVELENGTHS_NM=(600,650,700,750)
SIX_BAND_GAS_WAVELENGTHS_NM=(550,575,600,650,700,750)
EXTENDED_GAS_WAVELENGTHS_NM=(575,600,650,700,750)
AVOGADRO=6.02214076e23
R_D=287.05
M_H2O=18.01528e-3
M_DRY_AIR=28.9647e-3
M_O3=47.9982e-3
BOLTZMANN=1.380649e-23

# Pressure-level heights are rounded by different GRIB decoders and by the
# route interpolation step.  A small physical tolerance prevents a boundary
# touch from becoming a false NO_PROFILE_VERTICAL_BRACKET, while still
# refusing any extrapolation beyond the real profile.
DEFAULT_PROFILE_BOUNDARY_TOLERANCE_KM = 0.01


from .hitran_readiness import hitran_backend_status, resolve_hitran_db_path, resolve_hitran_lut_path

def _coerce_temperature_kelvin(value):
    """Return a physically plausible Kelvin temperature or NaN.

    Live Open-Meteo data are converted to Kelvin at the provider boundary.  This
    defensive helper also accepts legacy/current-CASE Celsius values so a stale
    cache or older archive cannot crash gas RT.
    """
    try:
        t=float(value)
    except (TypeError, ValueError):
        return np.nan
    if not math.isfinite(t):
        return np.nan
    if 150.0 <= t <= 350.0:
        return t
    if -123.15 <= t <= 76.85:
        return t + 273.15
    return np.nan


def _sat_vapor_pressure_hpa(tk):
    """Bolton/Tetens saturation vapour pressure with fail-closed bounds.

    The old implementation could receive Celsius while assuming Kelvin, placing
    the denominator near zero and causing math.exp overflow.  Gas RT must never
    abort the entire Firecloud analysis because of one malformed temperature.
    """
    tk=_coerce_temperature_kelvin(tk)
    if pd.isna(tk):
        return np.nan
    # This empirical form is intended for normal atmospheric temperatures.
    tk=min(330.0,max(180.0,float(tk)))
    tc=tk-273.15
    exponent=(17.67*tc)/(tc+243.5)
    # Guard is intentionally conservative; valid atmospheric inputs are far
    # inside this range, while malformed values fail without OverflowError.
    exponent=min(80.0,max(-80.0,exponent))
    return 6.112*math.exp(exponent)


def _cams_o3_at_pressure(o3row, pressure_hpa: float):
    """Return real CAMS O3 mass mixing ratio at a requested pressure level.

    Direct native levels are preferred. Missing intermediate levels are filled
    only by log-pressure interpolation between two *real* CAMS pressure-level
    ozone values. No extrapolation beyond the native profile and no climatology
    or total-column reconstruction is allowed.
    """
    if o3row is None:
        return np.nan, "CAMS_O3_MISSING", ""
    p=float(pressure_hpa)
    direct=o3row.get(f"cams_ozone_kgkg_{int(p)}hPa",np.nan)
    try:
        q=float(direct)
    except (TypeError,ValueError):
        q=np.nan
    if math.isfinite(q) and q>=0:
        return q, "CAMS_PRESSURE_LEVEL_OZONE_NATIVE", f"{int(p)}"
    pairs=[]
    for k,v in o3row.items():
        if not str(k).startswith("cams_ozone_kgkg_") or not str(k).endswith("hPa"):
            continue
        try:
            pp=float(str(k).split("cams_ozone_kgkg_",1)[1].split("hPa",1)[0]); qq=float(v)
        except (TypeError,ValueError):
            continue
        if math.isfinite(pp) and math.isfinite(qq) and pp>0 and qq>=0:
            pairs.append((pp,qq))
    pairs=sorted(set(pairs), key=lambda x:x[0])
    if len(pairs)<2 or p<pairs[0][0] or p>pairs[-1][0]:
        return np.nan, "CAMS_O3_MISSING", ""
    for (p0,q0),(p1,q1) in zip(pairs[:-1],pairs[1:]):
        if p0 <= p <= p1 and p1>p0:
            w=(math.log(p)-math.log(p0))/(math.log(p1)-math.log(p0))
            return q0+w*(q1-q0), "CAMS_PRESSURE_LEVEL_OZONE_INTERPOLATED_LOGP", f"{int(p0)}-{int(p1)}"
    return np.nan, "CAMS_O3_MISSING", ""


def build_gas_profile(snapshot:pd.DataFrame, pressure_levels_hpa, surface_elevation_m:float|None=None, ozone_snapshot:pd.DataFrame|None=None)->pd.DataFrame:
    """Build route T/P/H2O/O2/O3 atmospheric state.

    V8.4.1 binds *real* CAMS pressure-level ozone mass mixing ratio to the
    existing Open-Meteo thermodynamic pressure profile. No fixed 300 DU value,
    no standard/synthetic ozone profile, and no interpolation from a total
    column is permitted. Missing CAMS ozone therefore remains Missing.
    """
    ozone_by_point={}
    if ozone_snapshot is not None and not ozone_snapshot.empty and "point_id" in ozone_snapshot.columns:
        ozone_by_point={r.get("point_id"):r for _,r in ozone_snapshot.iterrows()}
    rows=[]
    for _,r in snapshot.iterrows():
        surf=float(r.get("model_surface_elevation_m",0.0) if pd.notna(r.get("model_surface_elevation_m",np.nan)) else 0.0)
        o3row=ozone_by_point.get(r.get("point_id"))
        for p in pressure_levels_hpa:
            z=r.get(f"geopotential_height_{p}hPa",np.nan); rh=r.get(f"relative_humidity_{p}hPa",np.nan); tk=r.get(f"temperature_{p}hPa",np.nan)
            if pd.isna(z): continue
            if pd.isna(tk):
                agl=max(0.0,(float(z)-surf)/1000.0); tk=max(190.0,288.15-6.5*agl); tq="STANDARD_LAPSE_FALLBACK"
            else:
                raw_tk=tk
                tk=_coerce_temperature_kelvin(raw_tk)
                if pd.isna(tk):
                    tq="INVALID_TEMPERATURE_MISSING"
                elif float(raw_tk) < 150.0:
                    tq="LEGACY_CELSIUS_CONVERTED_TO_KELVIN"
                else:
                    tq="FORECAST_PRESSURE_LEVEL_KELVIN"
            h2o=np.nan
            if pd.notna(rh) and pd.notna(tk):
                try:
                    rh_f=min(100.0,max(0.0,float(rh)))
                    es=_sat_vapor_pressure_hpa(tk)
                    if pd.notna(es):
                        e=max(0.0,min(float(p)*0.99,float(es)*rh_f/100.0))
                        h2o=e/max(1e-9,float(p))
                except (TypeError, ValueError, OverflowError):
                    h2o=np.nan

            o3_q=np.nan; o3_x=np.nan; o3_n=np.nan
            o3_q,o3q,o3_bracket=_cams_o3_at_pressure(o3row,float(p))
            if pd.notna(o3_q):
                # CAMS ozone is mass mixing ratio kg(O3)/kg(air). For a trace
                # constituent, mole fraction x ~= q * M_air / M_O3.
                o3_x=float(o3_q)*M_DRY_AIR/M_O3
                if pd.notna(tk) and float(tk)>0:
                    n_air=(float(p)*100.0)/(BOLTZMANN*float(tk))
                    o3_n=o3_x*n_air

            thermo_source=str(r.get("pressure_profile_primary_source", r.get("vertical_profile_source", "OPEN_METEO_PRESSURE_LEVEL")) or "OPEN_METEO_PRESSURE_LEVEL")
            source=(f"{thermo_source}+CAMS_O3+HITRAN_CONTRACT" if pd.notna(o3_x)
                    else f"{thermo_source}+O3_MISSING+HITRAN_CONTRACT")
            rows.append({
                "point_id":r.get("point_id"),"distance_km":r.get("distance_km"),"direction_offset_deg":r.get("direction_offset_deg"),
                "pressure_hpa":float(p),"altitude_agl_km":max(0.0,(float(z)-surf)/1000.0),"temperature_k":float(tk),
                "relative_humidity_pct":rh,"h2o_mole_fraction":h2o,"o2_mole_fraction":0.20946,
                "o3_mass_mixing_ratio_kgkg":o3_q,"o3_mole_fraction":o3_x,"o3_number_density_m3":o3_n,
                "o3_quality":o3q,"o3_source_pressure_bracket_hpa":o3_bracket,
                "temperature_quality":tq,"thermodynamic_profile_source":thermo_source,"gas_profile_source":source})
    return pd.DataFrame(rows)


@lru_cache(maxsize=8)
def _local_band_coefficients_cached(path: str, mtime_ns: int, size: int):
    try:
        df = pd.read_csv(path)
    except Exception:
        return pd.DataFrame()
    need={"wavelength_nm","gas","sigma_cm2_molecule"}
    return df if need.issubset(df.columns) else pd.DataFrame()

def _local_band_coefficients_from_csv(db_path: str | None = None):
    """Load the derived HITRAN runtime LUT; raw line tables are not needed at runtime.

    An explicit db_path keeps backward compatibility.  Otherwise V8.4.4 resolves
    FIRECLOUD_HITRAN_LUT_PATH, a packaged hitran_runtime LUT, then the legacy DB.
    """
    if db_path:
        path = os.path.join(db_path, "firecloud_600_750nm_band_coefficients.csv")
    else:
        path = str(resolve_hitran_lut_path()[0])
    if not os.path.exists(path): return pd.DataFrame()
    try:
        st=os.stat(path)
        return _local_band_coefficients_cached(os.path.abspath(path), int(st.st_mtime_ns), int(st.st_size)).copy()
    except Exception:
        return pd.DataFrame()


def _sigma_for_state(coeff: pd.DataFrame, gas: str, wavelength_nm: float, temperature_k: float, pressure_hpa: float) -> float:
    """Select/interpolate a HITRAN-derived band cross section for one atmospheric state.

    The local table may contain a single coefficient per gas/band or a T/P LUT.
    No extrapolated/fabricated coefficient is generated: nearest real LUT state is
    used when T/P dimensions exist, and the provenance remains HITRAN-derived.
    """
    c=coeff[(coeff["gas"].astype(str).str.upper()==gas.upper()) & np.isclose(pd.to_numeric(coeff["wavelength_nm"],errors="coerce"),float(wavelength_nm))].copy()
    if c.empty: return np.nan
    sig=pd.to_numeric(c["sigma_cm2_molecule"],errors="coerce")
    c=c[sig.notna()].copy(); c["sigma_cm2_molecule"]=sig[sig.notna()]
    if c.empty: return np.nan
    if "temperature_k" in c and pd.to_numeric(c["temperature_k"],errors="coerce").notna().any():
        dt=(pd.to_numeric(c["temperature_k"],errors="coerce")-float(temperature_k)).abs()/50.0
    else: dt=pd.Series(0.0,index=c.index)
    if "pressure_hpa" in c and pd.to_numeric(c["pressure_hpa"],errors="coerce").notna().any():
        pp=pd.to_numeric(c["pressure_hpa"],errors="coerce").clip(lower=1e-6)
        dp=(np.log(pp)-math.log(max(1e-6,float(pressure_hpa)))).abs()
    else: dp=pd.Series(0.0,index=c.index)
    idx=(dt.fillna(0)+dp.fillna(0)).idxmin()
    return float(c.loc[idx,"sigma_cm2_molecule"])*1e-4  # cm2/molecule -> m2/molecule


def _interp_profile_state(g: pd.DataFrame, altitude_km: float):
    """Linear vertical interpolation inside a real forecast gas profile; no extrapolation."""
    if g.empty: return None
    x=g.copy().sort_values("altitude_agl_km")
    z=pd.to_numeric(x["altitude_agl_km"],errors="coerce").to_numpy(float)
    good=np.isfinite(z)
    if not good.any() or altitude_km < np.nanmin(z[good]) or altitude_km > np.nanmax(z[good]): return None
    rec={}
    for c in ("temperature_k","pressure_hpa","o2_mole_fraction","h2o_mole_fraction","o3_mole_fraction"):
        y=pd.to_numeric(x.get(c,pd.Series(np.nan,index=x.index)),errors="coerce").to_numpy(float)
        m=np.isfinite(z)&np.isfinite(y)
        if m.sum()<2: return None
        rec[c]=float(np.interp(float(altitude_km),z[m],y[m]))
    return rec


def active_gas_wavelengths(coeff: pd.DataFrame) -> tuple[int, ...]:
    """Return only production bands that have a complete real LUT grid.

    R3.2 supports the frozen six-band contract. 550/575 nm are enabled only
    when every gas has the full real T/P grid. Missing spectroscopy is never
    interpolated from neighbouring diagnostic bands.
    """
    if coeff is None or coeff.empty or "gas" not in coeff or "wavelength_nm" not in coeff:
        return GAS_WAVELENGTHS_NM
    required_t=(220.0,250.0,280.0,293.0)
    required_p=(100.0,300.0,500.0,700.0,900.0,1000.0)
    required_tp={(float(t),float(p)) for t in required_t for p in required_p}
    def band_complete(wl: float) -> bool:
        for gas in ("O3","O2","H2O"):
            mask=(coeff["gas"].astype(str).str.upper().str.strip().eq(gas) &
                  np.isclose(pd.to_numeric(coeff["wavelength_nm"],errors="coerce"),float(wl),equal_nan=False))
            if not mask.any(): return False
            sub=coeff.loc[mask].copy()
            if not {"temperature_k","pressure_hpa","sigma_cm2_molecule"}.issubset(sub.columns): return False
            for c in ("temperature_k","pressure_hpa","sigma_cm2_molecule"):
                sub[c]=pd.to_numeric(sub[c],errors="coerce")
            valid=sub["sigma_cm2_molecule"].notna() & np.isfinite(sub["sigma_cm2_molecule"]) & (sub["sigma_cm2_molecule"]>=0)
            tp=set(zip(sub.loc[valid,"temperature_k"],sub.loc[valid,"pressure_hpa"]))
            if not required_tp.issubset(tp): return False
        return True
    has575=band_complete(575.0)
    has550=band_complete(550.0)
    if has550 and has575:
        return SIX_BAND_GAS_WAVELENGTHS_NM
    if has575:
        return EXTENDED_GAS_WAVELENGTHS_NM
    return GAS_WAVELENGTHS_NM


def _prepare_fast_lut(coeff: pd.DataFrame, wavelengths=GAS_WAVELENGTHS_NM):
    """Convert the small Runtime LUT to NumPy arrays for hot-loop lookup.

    V8.4.6.2 removes repeated pandas filtering from every ray segment.  Selection
    semantics are identical to _sigma_for_state: nearest real LUT state under
    |dT|/50 + |dlnP|, with no fabricated/extrapolated coefficient.
    """
    lut={}
    c=coeff.copy()
    c["gas"]=c["gas"].astype(str).str.upper()
    c["wavelength_nm"]=pd.to_numeric(c["wavelength_nm"],errors="coerce")
    c["sigma_cm2_molecule"]=pd.to_numeric(c["sigma_cm2_molecule"],errors="coerce")
    c["temperature_k"]=pd.to_numeric(c.get("temperature_k",np.nan),errors="coerce")
    c["pressure_hpa"]=pd.to_numeric(c.get("pressure_hpa",np.nan),errors="coerce")
    for gas in ("O3","O2","H2O"):
        for wl in wavelengths:
            q=c[(c["gas"]==gas)&np.isclose(c["wavelength_nm"],float(wl))].dropna(subset=["sigma_cm2_molecule"])
            if q.empty:
                continue
            t=q["temperature_k"].to_numpy(float)
            p=q["pressure_hpa"].to_numpy(float)
            sig=q["sigma_cm2_molecule"].to_numpy(float)*1e-4
            lut[(gas,int(wl))]=(t,p,np.log(np.clip(p,1e-6,None)),sig)
    return lut


def _sigma_fast(lut, gas: str, wl: int, tk: float, p_hpa: float) -> float:
    rec=lut.get((gas,int(wl)))
    if rec is None:
        return np.nan
    t,p,lnp,sig=rec
    if len(sig)==1:
        return float(sig[0])
    dt=np.where(np.isfinite(t),np.abs(t-float(tk))/50.0,0.0)
    dp=np.where(np.isfinite(p),np.abs(lnp-math.log(max(1e-6,float(p_hpa)))),0.0)
    return float(sig[int(np.argmin(dt+dp))])


def _prepare_fast_profile(gas_profile: pd.DataFrame):
    """Index route gas profiles once per direction/distance using NumPy arrays."""
    prepared={}
    p=gas_profile.copy()
    for direction,gdir in p.groupby("direction_offset_deg",sort=False):
        by_distance={}
        for distance,g in gdir.groupby("distance_km",sort=False):
            x=g.sort_values("altitude_agl_km")
            z=pd.to_numeric(x["altitude_agl_km"],errors="coerce").to_numpy(float)
            rec={"z":z}
            for col in ("temperature_k","pressure_hpa","o2_mole_fraction","h2o_mole_fraction","o3_mole_fraction"):
                rec[col]=pd.to_numeric(x[col],errors="coerce").to_numpy(float)
            by_distance[float(distance)]=rec
        distances=np.array(sorted(by_distance),dtype=float)
        prepared[float(direction)]={"distances":distances,"profiles":by_distance}
    return prepared


def _interp_fast_profile_state(rec, altitude_km: float):
    z=rec["z"]
    good_z=np.isfinite(z)
    if not good_z.any() or altitude_km < np.nanmin(z[good_z]) or altitude_km > np.nanmax(z[good_z]):
        return None
    out={}
    for col in ("temperature_k","pressure_hpa","o2_mole_fraction","h2o_mole_fraction","o3_mole_fraction"):
        y=rec[col]
        m=np.isfinite(z)&np.isfinite(y)
        if m.sum()<2:
            return None
        out[col]=float(np.interp(float(altitude_km),z[m],y[m]))
    return out


def _ray_altitudes_matrix(target_distance_km: float, target_altitudes_km, sample_distances_km,
                          solar_altitude_deg: float, earth_radius_km: float = 6371.0):
    return ray_altitude_matrix_km(target_distance_km, target_altitudes_km, sample_distances_km, solar_altitude_deg, earth_radius_km)

def _interp_profile_vectors(rec, altitudes_km):
    """Vector-interpolate one real route profile at many ray altitudes.

    No vertical extrapolation is introduced. A row is valid only when all five
    gas-state quantities can be interpolated from at least two real profile
    levels, matching the scalar V8.4.6.2 semantics.
    """
    q=np.asarray(altitudes_km,dtype=float)
    out={}; valid=np.isfinite(q)
    z=np.asarray(rec["z"],dtype=float)
    good_z=np.isfinite(z)
    if not good_z.any():
        return {}, np.zeros(q.shape,dtype=bool)
    valid &= (q >= np.nanmin(z[good_z])) & (q <= np.nanmax(z[good_z]))
    for col in ("temperature_k","pressure_hpa","o2_mole_fraction","h2o_mole_fraction","o3_mole_fraction"):
        y=np.asarray(rec[col],dtype=float)
        m=np.isfinite(z)&np.isfinite(y)
        if m.sum()<2:
            return {}, np.zeros(q.shape,dtype=bool)
        vals=np.full(q.shape,np.nan,dtype=float)
        if valid.any():
            vals[valid]=np.interp(q[valid],z[m],y[m])
        out[col]=vals
        valid &= np.isfinite(vals)
    return out, valid


def _sigma_fast_vector(lut, gas: str, wl: int, tk, p_hpa):
    """Vector form of _sigma_fast with identical nearest-real-state metric."""
    rec=lut.get((gas,int(wl)))
    tk=np.asarray(tk,dtype=float); p_hpa=np.asarray(p_hpa,dtype=float)
    ans=np.full(tk.shape,np.nan,dtype=float)
    if rec is None:
        return ans
    t,p,lnp,sig=rec
    valid=np.isfinite(tk)&np.isfinite(p_hpa)&(p_hpa>0)
    if not valid.any():
        return ans
    if len(sig)==1:
        ans[valid]=float(sig[0]); return ans
    tv=tk[valid,None]; pv=np.log(np.maximum(1e-6,p_hpa[valid]))[:,None]
    dt=np.where(np.isfinite(t)[None,:],np.abs(tv-t[None,:])/50.0,0.0)
    dp=np.where(np.isfinite(p)[None,:],np.abs(pv-lnp[None,:]),0.0)
    idx=np.argmin(dt+dp,axis=1)
    ans[valid]=sig[idx]
    return ans


@dataclass(frozen=True)
class GasRTPreparedContext:
    """Reusable, angle-independent gas RT preparation.

    R3.3 separates expensive-but-static preparation (Runtime LUT decode, fast LUT
    arrays, route profile indexing) from the angle-specific slant-ray integration.
    The context contains no solar geometry and therefore is safe to reuse across
    all core angles that share the same forecast/CAMS atmospheric state.
    """
    coeff: pd.DataFrame
    wavelengths: tuple[int, ...]
    lut: dict
    prepared_profile: dict
    valid: bool
    failure_cause: str = ""


def prepare_gas_rt_context(gas_profile: pd.DataFrame, db_path: str | None = None) -> GasRTPreparedContext:
    coeff=_local_band_coefficients_from_csv(db_path)
    wavelengths=active_gas_wavelengths(coeff)
    if coeff.empty:
        return GasRTPreparedContext(coeff, tuple(wavelengths), {}, {}, False, "HITRAN_LOCAL_BAND_TABLE_MISSING")
    c=coeff.copy(); c["gas"]=c["gas"].astype(str).str.upper()
    complete=all(((c["gas"]==g)&np.isclose(pd.to_numeric(c["wavelength_nm"],errors="coerce"),wl)).any()
                 for g in ("O3","O2","H2O") for wl in wavelengths)
    if not complete:
        return GasRTPreparedContext(c, tuple(wavelengths), {}, {}, False, "HITRAN_BAND_TABLE_INCOMPLETE")
    required={"distance_km","direction_offset_deg","altitude_agl_km","temperature_k","pressure_hpa","o2_mole_fraction","h2o_mole_fraction","o3_mole_fraction"}
    if gas_profile is None or gas_profile.empty:
        # Preserve the legacy public failure label used by diagnostic callers
        # that invoke gas RT without any atmospheric profile at all. PhysicsCore
        # runtime supplies a real profile and therefore does not enter this path.
        return GasRTPreparedContext(c, tuple(wavelengths), {}, {}, False, "HITRAN_LOCAL_BAND_TABLE_MISSING")
    if not required.issubset(gas_profile.columns):
        return GasRTPreparedContext(c, tuple(wavelengths), {}, {}, False, "ATMOSPHERIC_GAS_PROFILE_INCOMPLETE")
    return GasRTPreparedContext(c, tuple(wavelengths), _prepare_fast_lut(c,wavelengths), _prepare_fast_profile(gas_profile), True, "")


def integrate_gas_sun_to_targets(targets:pd.DataFrame, gas_profile:pd.DataFrame, solar_altitude_deg:float, db_path:str|None=None, earth_radius_km:float=6371.0, progress_callback=None, prepared_context: GasRTPreparedContext | None = None)->pd.DataFrame:
    """Hybrid gas RT with physics-aware applicability and model-top termination.

    V8.4.9 separates three states that older versions conflated as Missing:
      * EARTH_SHADOW: no direct solar ray exists, so spectral Sun->cloud RT is N/A;
      * MODEL_TOP_TERMINATED: the direct ray has left the pressure-profile-supported
        gas domain, so integration is complete *within the configured gas model*;
      * TRUE MISSING: target/profile/domain data needed by an applicable ray is absent.

    The numerical gas absorption inside supported pressure-profile segments is
    unchanged from V8.4.8. No gas is invented above the real profile top.
    """
    out=targets.copy()
    ctx = prepared_context if prepared_context is not None else prepare_gas_rt_context(gas_profile, db_path)
    coeff=ctx.coeff
    wavelengths=ctx.wavelengths
    for wl in wavelengths:
        for gas in ("o3","o2","h2o"):
            out[f"gas_tau_{gas}_{wl}nm"]=np.nan
        out[f"gas_tau_{wl}nm"]=np.nan
        out[f"gas_transmission_{wl}nm"]=np.nan
        out[f"o3_transmission_{wl}nm"]=np.nan
    out["gas_path_completeness"]=0.0
    out["gas_rt_quality"]="HITRAN_LOCAL_BAND_TABLE_MISSING"
    out["gas_rt_failure_cause"]="HITRAN_LOCAL_BAND_TABLE_MISSING"
    out["gas_rt_domain_status"]="MISSING"
    out["gas_profile_top_km"]=np.nan
    out["gas_rt_boundary_clipped"]=False
    out["gas_rt_expected_termination"]=""
    out["rt_applicable_direct_solar"]=True
    if "geometric_illuminated_fraction" in out.columns:
        gf=pd.to_numeric(out["geometric_illuminated_fraction"],errors="coerce")
        out["rt_applicable_direct_solar"]=(gf.fillna(0.0)>0.0)
    if not ctx.valid:
        out["gas_rt_quality"]=ctx.failure_cause or "HITRAN_LOCAL_BAND_TABLE_MISSING"
        out["gas_rt_failure_cause"]=ctx.failure_cause or "HITRAN_LOCAL_BAND_TABLE_MISSING"
        return out

    lut=ctx.lut
    prepared=ctx.prepared_profile
    try:
        boundary_tol=max(1.0e-6, float(os.getenv(
            "FIRECLOUD_GAS_PROFILE_BOUNDARY_TOLERANCE_KM",
            str(DEFAULT_PROFILE_BOUNDARY_TOLERANCE_KM),
        )))
    except Exception:
        boundary_tol=DEFAULT_PROFILE_BOUNDARY_TOLERANCE_KM

    group_items=list(out.groupby(["direction_offset_deg","distance_km"],sort=False,dropna=False).groups.items())
    total_groups=max(1,len(group_items))
    emit_every=max(1,total_groups//12)
    if progress_callback is not None:
        try: progress_callback(0.0, f"氣體光路積分 0/{total_groups}")
        except Exception: pass

    for _gi, ((direction,td), idx) in enumerate(group_items):
        if progress_callback is not None and (_gi % emit_every == 0):
            try: progress_callback(float(_gi)/total_groups, f"氣體光路積分 {_gi}/{total_groups}")
            except Exception: pass
        ii=np.asarray(list(idx))
        tz=pd.to_numeric(out.loc[ii,"voxel_center_km"] if "voxel_center_km" in out.columns else out.loc[ii,"altitude_agl_km"],errors="coerce").to_numpy(float)
        applicable=out.loc[ii,"rt_applicable_direct_solar"].astype(bool).to_numpy()
        try:
            direction_f=float(direction); td_f=float(td)
        except (TypeError,ValueError):
            out.loc[ii,"gas_rt_quality"]="HITRAN_3D_GAS_PATH_MISSING"
            out.loc[ii,"gas_rt_failure_cause"]="TARGET_OR_DIRECTION_OUTSIDE_GAS_ROUTE"
            out.loc[ii,"gas_rt_domain_status"]="TRUE_DATA_MISSING"
            continue
        drec=prepared.get(direction_f)
        if drec is None or not math.isfinite(td_f):
            out.loc[ii,"gas_rt_quality"]="HITRAN_3D_GAS_PATH_MISSING"
            out.loc[ii,"gas_rt_failure_cause"]="NO_ROUTE_PROFILE_SAMPLE"
            out.loc[ii,"gas_rt_domain_status"]="TRUE_DATA_MISSING"
            continue

        all_ds=drec["distances"]
        i0=int(np.searchsorted(all_ds,td_f-1e-9,side="left")); ds=all_ds[i0:]
        target_rec=drec["profiles"].get(float(all_ds[i0])) if i0 < len(all_ds) else None
        if target_rec is not None and np.isfinite(target_rec["z"]).any():
            target_top=float(np.nanmax(target_rec["z"])); target_bottom=float(np.nanmin(target_rec["z"]))
            out.loc[ii,"gas_profile_top_km"]=target_top
        else:
            target_top=np.nan; target_bottom=np.nan

        # Earth-shadowed voxels have no direct Sun->target path. They are N/A, not Missing.
        shadowed=~applicable
        if shadowed.any():
            out.loc[ii[shadowed],"gas_rt_quality"]="NOT_APPLICABLE_EARTH_SHADOW"
            out.loc[ii[shadowed],"gas_rt_failure_cause"]="EARTH_SHADOW_NO_DIRECT_SOLAR_RAY"
            out.loc[ii[shadowed],"gas_rt_domain_status"]="NOT_APPLICABLE"
            out.loc[ii[shadowed],"gas_rt_expected_termination"]="EARTH_SHADOW"
            out.loc[ii[shadowed],"gas_path_completeness"]=1.0

        above_target=np.zeros(len(ii),dtype=bool)
        below_target=np.zeros(len(ii),dtype=bool)
        if math.isfinite(target_top): above_target=applicable & (tz > target_top + boundary_tol)
        if math.isfinite(target_bottom): below_target=applicable & (tz < target_bottom - boundary_tol)
        if above_target.any():
            out.loc[ii[above_target],"gas_rt_quality"]="HITRAN_3D_GAS_PATH_MISSING"
            out.loc[ii[above_target],"gas_rt_failure_cause"]="TARGET_ABOVE_GAS_PROFILE_TOP"
            out.loc[ii[above_target],"gas_rt_domain_status"]="TRUE_VERTICAL_DATA_MISSING"
        if below_target.any():
            out.loc[ii[below_target],"gas_rt_quality"]="HITRAN_3D_GAS_PATH_MISSING"
            out.loc[ii[below_target],"gas_rt_failure_cause"]="TARGET_BELOW_GAS_PROFILE_BOTTOM"
            out.loc[ii[below_target],"gas_rt_domain_status"]="TRUE_VERTICAL_DATA_MISSING"

        solve=applicable & ~above_target & ~below_target
        if len(ds)<2:
            if solve.any():
                out.loc[ii[solve],"gas_rt_quality"]="HITRAN_3D_GAS_PATH_MISSING"
                out.loc[ii[solve],"gas_rt_failure_cause"]="DYNAMIC_RT_DOMAIN_EXHAUSTED"
                out.loc[ii[solve],"gas_rt_domain_status"]="TRUE_ROUTE_DOMAIN_MISSING"
            continue

        n=len(ii)
        used=np.zeros(n,dtype=int)
        required_seg=np.zeros(n,dtype=int)
        model_top_exit=np.zeros(n,dtype=bool)
        model_bottom_exit=np.zeros(n,dtype=bool)
        profile_gap=np.zeros(n,dtype=bool)
        gas_state_gap=np.zeros(n,dtype=bool)
        geometry_gap=np.zeros(n,dtype=bool)
        boundary_clipped=np.zeros(n,dtype=bool)
        taus={wl:{g:np.zeros(n,dtype=float) for g in ("O3","O2","H2O")} for wl in wavelengths}
        zedge=_ray_altitudes_matrix(td_f,tz,ds,solar_altitude_deg,earth_radius_km)
        mids=0.5*(ds[:-1]+ds[1:])
        zmid=_ray_altitudes_matrix(td_f,tz,mids,solar_altitude_deg,earth_radius_km)

        # A negative-altitude solar ray normally leaves the real atmosphere
        # after only a fraction of the requested Dynamic route.  Older code
        # continued scanning every remaining route segment for every target
        # distance, even after all applicable rows had already crossed the
        # model top.  With ~1,000 route groups this turns the RT stage into an
        # avoidable O(groups * route_length) hot loop and looks like a stall at
        # the first angle.  Once a row is known to be outside the supported
        # profile, no later segment can contribute to its Sun->target path.
        for j,(d0,d1) in enumerate(zip(ds[:-1],ds[1:])):
            active = solve & ~model_top_exit & ~model_bottom_exit & ~profile_gap
            if not active.any():
                break
            rec=drec["profiles"][float(d0)]
            rz=np.asarray(rec["z"],dtype=float)
            finite_z=np.isfinite(rz)
            if not finite_z.any():
                # This route segment lies inside an applicable ray but the real
                # pressure profile is unavailable. Count it as required so the
                # completeness metric cannot remain falsely at 1.0.
                required_seg[solve] += 1
                profile_gap |= solve
                continue
            lo=float(np.nanmin(rz[finite_z])); hi=float(np.nanmax(rz[finite_z]))
            z0=zedge[:,j]; z1=zedge[:,j+1]
            finite_edge=np.isfinite(z0)&np.isfinite(z1)
            geometry_gap |= active & ~finite_edge
            required_seg[active & ~finite_edge] += 1
            seg_low=np.minimum(z0,z1)
            seg_high=np.maximum(z0,z1)
            above=active & finite_edge & (seg_low > hi+boundary_tol)
            below=active & finite_edge & (seg_high < lo-boundary_tol)
            # Integrate only the part of a segment that lies inside the real
            # profile. This removes the old midpoint-only failure at a pressure
            # level boundary without extrapolating any gas state.
            overlap=active & finite_edge & (seg_high >= lo-boundary_tol) & (seg_low <= hi+boundary_tol)
            delta=z1-z0
            nonflat=finite_edge & (np.abs(delta)>1e-12)
            u_a=np.zeros(n,dtype=float); u_b=np.ones(n,dtype=float)
            if nonflat.any():
                u_lo=(lo-z0[nonflat])/delta[nonflat]
                u_hi=(hi-z0[nonflat])/delta[nonflat]
                u_a[nonflat]=np.minimum(u_lo,u_hi)
                u_b[nonflat]=np.maximum(u_lo,u_hi)
            u_enter=np.clip(u_a,0.0,1.0)
            u_exit=np.clip(u_b,0.0,1.0)
            fraction=np.maximum(0.0,u_exit-u_enter)
            within=overlap & (fraction>1e-12)
            model_top_exit |= above | (active & finite_edge & (z0 <= hi+boundary_tol) & (z1 > hi+boundary_tol))
            # A ray leaving through the bottom of the real pressure profile is
            # a finite model/ground termination, not a missing vertical bracket.
            # The segment is still clipped to the supported interval above.
            model_bottom_exit |= below | (active & finite_edge & (z0 >= lo-boundary_tol) & (z1 < lo-boundary_tol))
            # Segments below the lowest real pressure level are outside the
            # supported atmosphere. They are handled as a finite bottom exit,
            # not as an invented gas segment or a missing-data denominator.
            required_seg[within] += 1
            if not within.any():
                continue

            qclip=z0 + delta*0.5*(u_enter+u_exit)
            state,valid=_interp_profile_vectors(rec,qclip)
            valid &= within & np.isfinite(z0)&np.isfinite(z1)
            gas_state_gap |= within & ~valid
            boundary_clipped |= within & (fraction < 1.0-1e-9)
            if not valid.any():
                profile_gap |= within
                continue
            path_m=np.hypot((float(d1)-float(d0))*1000.0,(z1-z0)*1000.0)*fraction
            tk=state["temperature_k"]; ph=state["pressure_hpa"]
            valid &= np.isfinite(ph)&np.isfinite(tk)&(tk>0)
            n_air=np.full(n,np.nan,dtype=float); n_air[valid]=ph[valid]*100.0/(BOLTZMANN*tk[valid])
            dens={"O2":state["o2_mole_fraction"]*n_air,"H2O":state["h2o_mole_fraction"]*n_air,"O3":state["o3_mole_fraction"]*n_air}
            for arr in dens.values(): valid &= np.isfinite(arr)
            if not valid.any():
                profile_gap |= within
                continue
            segment_ok=valid.copy(); segment_tau={}
            for wl in wavelengths:
                for gas,density in dens.items():
                    sigma=_sigma_fast_vector(lut,gas,wl,tk,ph)
                    segment_ok &= np.isfinite(sigma)
                    segment_tau[(wl,gas)]=sigma*density*path_m
            failed_required=within & ~segment_ok
            profile_gap |= failed_required
            if not segment_ok.any():
                continue
            used[segment_ok]+=1
            for (wl,gas),arr in segment_tau.items():
                taus[wl][gas][segment_ok]+=arr[segment_ok]

        have=used>0
        completeness=np.ones(n,dtype=float)
        reqpos=required_seg>0
        completeness[reqpos]=used[reqpos].astype(float)/required_seg[reqpos].astype(float)
        completeness[~solve]=np.where(shadowed[~solve],1.0,0.0)

        for wl in wavelengths:
            total_tau=np.zeros(n,dtype=float)
            for gas in ("O3","O2","H2O"):
                vals=np.where(have,taus[wl][gas],np.nan)
                out.loc[ii,f"gas_tau_{gas.lower()}_{wl}nm"]=vals
                total_tau += taus[wl][gas]
            total_tau=np.where(have,total_tau,np.nan)
            out.loc[ii,f"gas_tau_{wl}nm"]=total_tau
            out.loc[ii,f"gas_transmission_{wl}nm"]=np.exp(-total_tau)
            out.loc[ii,f"o3_transmission_{wl}nm"]=np.exp(-out.loc[ii,f"gas_tau_o3_{wl}nm"].to_numpy(float))
        out.loc[ii,"gas_path_completeness"]=completeness
        out.loc[ii,"gas_rt_boundary_clipped"]=boundary_clipped

        # Domain exhaustion only matters when an applicable ray is still inside the
        # supported profile at the final route edge. Rays that have crossed above
        # the profile top are model-top terminated, not route-Missing.
        final_rec=drec["profiles"][float(ds[-1])]
        fz=np.asarray(final_rec["z"],dtype=float); fgood=np.isfinite(fz)
        final_top=float(np.nanmax(fz[fgood])) if fgood.any() else np.nan
        zend=zedge[:,-1]
        exhausted=solve & np.isfinite(zend) & math.isfinite(final_top) & (zend <= final_top+boundary_tol) & ~model_top_exit & ~model_bottom_exit
        no_required=solve & (required_seg==0) & ~model_top_exit & ~model_bottom_exit
        profile_missing=solve & ((completeness<0.999) | profile_gap) & ~exhausted & ~model_bottom_exit
        success=solve & have & (completeness>=0.999) & ~exhausted & ~profile_missing
        missing_no_segment=solve & ~have & ~model_top_exit & ~model_bottom_exit & ~exhausted

        if success.any():
            out.loc[ii[success],"gas_rt_quality"]="HITRAN_DERIVED_3D_GAS_RT;MODEL_TOP_TERMINATED"
            out.loc[ii[success],"gas_rt_failure_cause"]=""
            out.loc[ii[success],"gas_rt_domain_status"]="MODEL_TOP_TERMINATED"
            out.loc[ii[success],"gas_rt_expected_termination"]="MODEL_TOP"
        bottom_success=success & model_bottom_exit
        if bottom_success.any():
            out.loc[ii[bottom_success],"gas_rt_quality"]="HITRAN_DERIVED_3D_GAS_RT;MODEL_BOTTOM_TERMINATED"
            out.loc[ii[bottom_success],"gas_rt_failure_cause"]=""
            out.loc[ii[bottom_success],"gas_rt_domain_status"]="MODEL_BOTTOM_TERMINATED"
            out.loc[ii[bottom_success],"gas_rt_expected_termination"]="MODEL_BOTTOM"
        if exhausted.any():
            ex_have=exhausted & have
            ex_none=exhausted & ~have
            if ex_have.any():
                out.loc[ii[ex_have],"gas_rt_quality"]="HITRAN_DERIVED_3D_GAS_RT;ROUTE_DOMAIN_TRUNCATED"
                out.loc[ii[ex_have],"gas_rt_failure_cause"]="DYNAMIC_RT_DOMAIN_EXHAUSTED"
                out.loc[ii[ex_have],"gas_rt_domain_status"]="TRUE_ROUTE_DOMAIN_MISSING"
            if ex_none.any():
                out.loc[ii[ex_none],"gas_rt_quality"]="HITRAN_3D_GAS_PATH_MISSING"
                out.loc[ii[ex_none],"gas_rt_failure_cause"]="DYNAMIC_RT_DOMAIN_EXHAUSTED"
                out.loc[ii[ex_none],"gas_rt_domain_status"]="TRUE_ROUTE_DOMAIN_MISSING"
        pm=profile_missing & ~above_target & ~below_target
        if pm.any():
            out.loc[ii[pm],"gas_rt_quality"]="HITRAN_3D_GAS_PATH_MISSING"
            out.loc[ii[pm],"gas_rt_failure_cause"]="NO_PROFILE_VERTICAL_BRACKET"
            out.loc[ii[pm],"gas_rt_domain_status"]="TRUE_VERTICAL_DATA_MISSING"
        ns=missing_no_segment & ~pm
        if ns.any():
            out.loc[ii[ns],"gas_rt_quality"]="HITRAN_3D_GAS_PATH_MISSING"
            out.loc[ii[ns],"gas_rt_failure_cause"]="NO_ROUTE_PROFILE_SAMPLE"
            out.loc[ii[ns],"gas_rt_domain_status"]="TRUE_DATA_MISSING"
        gg=geometry_gap & ~above_target & ~below_target
        if gg.any():
            out.loc[ii[gg],"gas_rt_quality"]="HITRAN_3D_GAS_PATH_MISSING"
            out.loc[ii[gg],"gas_rt_failure_cause"]="RAY_GEOMETRY_MISSING"
            out.loc[ii[gg],"gas_rt_domain_status"]="TRUE_GEOMETRY_DATA_MISSING"
        gs=pm & gas_state_gap
        if gs.any():
            out.loc[ii[gs],"gas_rt_failure_cause"]="GAS_STATE_VALUE_MISSING"
            out.loc[ii[gs],"gas_rt_domain_status"]="TRUE_GAS_STATE_DATA_MISSING"

        # A ray may start at the top of the supported profile and immediately
        # leave it. The supported-domain gas path then has zero length: tau=0,
        # transmission=1 is a valid model-domain result, not Missing.
        zero_supported=solve & ~have & (model_top_exit | model_bottom_exit) & ~exhausted & ~pm
        if zero_supported.any():
            for wl in wavelengths:
                for gas in ("o3","o2","h2o"):
                    out.loc[ii[zero_supported],f"gas_tau_{gas}_{wl}nm"]=0.0
                out.loc[ii[zero_supported],f"gas_tau_{wl}nm"]=0.0
                out.loc[ii[zero_supported],f"gas_transmission_{wl}nm"]=1.0
            out.loc[ii[zero_supported],"gas_path_completeness"]=1.0
            out.loc[ii[zero_supported],"gas_rt_quality"] = np.where(
                model_bottom_exit[zero_supported],
                "HITRAN_DERIVED_3D_GAS_RT;MODEL_BOTTOM_TERMINATED_ZERO_SUPPORTED_PATH",
                "HITRAN_DERIVED_3D_GAS_RT;MODEL_TOP_TERMINATED_ZERO_SUPPORTED_PATH",
            )
            out.loc[ii[zero_supported],"gas_rt_failure_cause"]=""
            out.loc[ii[zero_supported],"gas_rt_domain_status"] = np.where(
                model_bottom_exit[zero_supported], "MODEL_BOTTOM_TERMINATED", "MODEL_TOP_TERMINATED"
            )
            out.loc[ii[zero_supported],"gas_rt_expected_termination"] = np.where(
                model_bottom_exit[zero_supported], "MODEL_BOTTOM", "MODEL_TOP"
            )

        # Fail closed: a partially integrated tau may remain useful as a
        # diagnostic, but it must never masquerade as a complete gas
        # transmission. Any TRUE_* domain status therefore leaves the public
        # gas_transmission fields Missing, which propagates correctly into full RT.
        domain_now=out.loc[ii,"gas_rt_domain_status"].astype(str)
        true_missing=domain_now.str.startswith("TRUE_").to_numpy()
        if true_missing.any():
            for wl in wavelengths:
                out.loc[ii[true_missing],f"gas_transmission_{wl}nm"]=np.nan
    if progress_callback is not None:
        try: progress_callback(1.0, f"氣體光路積分 {total_groups}/{total_groups} 完成")
        except Exception: pass
    return out
