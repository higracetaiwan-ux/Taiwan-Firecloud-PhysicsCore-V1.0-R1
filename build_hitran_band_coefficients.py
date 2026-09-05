#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

O3_XSC_FILENAME = "O3_SerdyuchenkoGorshelev_213_1100nm.dat"
STATE_CACHE_DIRNAME = ".firecloud_lut_state_cache"
STATE_CACHE_FORMAT = "Taiwan Firecloud Hybrid Gas Spectroscopy Voigt state checkpoint"


def parse_args():
    p = argparse.ArgumentParser(description="Build Taiwan Firecloud hybrid 550–750 nm gas spectroscopy LUT")
    p.add_argument("--db", default="hitran_db")
    p.add_argument("--temperatures", default="220,250,280,293")
    p.add_argument("--pressures-hpa", default="100,300,500,700,900,1000")
    p.add_argument("--wavenumber-step", type=float, default=0.02)
    p.add_argument("--h2o-table", default="H2O_535_765")
    p.add_argument("--o2-table", default="O2_535_765")
    p.add_argument("--o3-xsc", default=O3_XSC_FILENAME)
    p.add_argument(
        "--wavelengths",
        default="550,575,600,650,700,750",
        help="Comma-separated diagnostic band centers in nm. PhysicsCore V1.0 runtime default is the full six-band grid.",
    )
    p.add_argument(
        "--v1-six-band", action="store_true",
        help="Build the PhysicsCore V1.0 six-band LUT at 550,575,600,650,700,750 nm. Requires local H2O/O2 tables extending to at least 535 nm and validated O3 XSC.",
    )
    args=p.parse_args()
    if args.v1_six_band:
        args.wavelengths="550,575,600,650,700,750"
    return args


def _file_fingerprint(path: Path) -> dict[str, object]:
    """Return a cheap input fingerprint for invalidating state checkpoints.

    The line-list files can be hundreds of megabytes, so hashing the whole file
    before every build would add an avoidable startup cost.  Size and nanosecond
    mtime are sufficient to invalidate normal replacement/download workflows;
    the table names and HAPI version are included in the build signature too.
    """
    stat = path.stat()
    return {"name": path.name, "size": int(stat.st_size), "mtime_ns": int(stat.st_mtime_ns)}


def _build_signature(
    *,
    temperatures: list[float],
    pressures: list[float],
    wavelengths: list[float],
    wavenumber_step: float,
    h2o_table: str,
    o2_table: str,
    input_fingerprints: dict[str, dict[str, object]],
    hapi_version: str,
) -> str:
    """Create the identity of one scientifically distinct LUT build."""
    payload = {
        "format": STATE_CACHE_FORMAT,
        "builder": "PhysicsCore-V1.0-R4.8",
        "temperatures_k": temperatures,
        "pressures_hpa": pressures,
        "wavelengths_nm": wavelengths,
        "wavenumber_step_cm-1": float(wavenumber_step),
        "h2o_table": h2o_table,
        "o2_table": o2_table,
        "input_fingerprints": input_fingerprints,
        "hapi_version": hapi_version,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _state_cache_path(cache_dir: Path, gas: str, temperature_k: float, pressure_hpa: float) -> Path:
    """Use readable, filesystem-safe names for individual T/P checkpoints."""
    def token(value: float) -> str:
        return f"{value:g}".replace("-", "m").replace(".", "p")

    return cache_dir / f"{gas}_T{token(temperature_k)}_P{token(pressure_hpa)}.json"


def _valid_cached_rows(
    payload: object,
    *,
    signature: str,
    gas: str,
    temperature_k: float,
    pressure_hpa: float,
    wavelengths: list[float],
) -> list[dict] | None:
    """Validate a checkpoint before allowing it into the final LUT."""
    if not isinstance(payload, dict) or payload.get("format") != STATE_CACHE_FORMAT:
        return None
    if payload.get("signature") != signature:
        return None
    rows = payload.get("rows")
    if not isinstance(rows, list) or len(rows) != len(wavelengths):
        return None
    expected_wavelengths = {float(w) for w in wavelengths}
    clean: list[dict] = []
    for row in rows:
        if not isinstance(row, dict):
            return None
        try:
            row_gas = str(row["gas"])
            row_wavelength = float(row["wavelength_nm"])
            row_temperature = float(row["temperature_k"])
            row_pressure = float(row["pressure_hpa"])
            sigma = float(row["sigma_cm2_molecule"])
        except (KeyError, TypeError, ValueError):
            return None
        if (
            row_gas != gas
            or row_temperature != float(temperature_k)
            or row_pressure != float(pressure_hpa)
            or row_wavelength not in expected_wavelengths
            or not np.isfinite(sigma)
            or sigma < 0
        ):
            return None
        clean.append(row)
    if {float(row["wavelength_nm"]) for row in clean} != expected_wavelengths:
        return None
    return clean


def _load_state_checkpoint(
    cache_dir: Path,
    *,
    signature: str,
    gas: str,
    temperature_k: float,
    pressure_hpa: float,
    wavelengths: list[float],
) -> list[dict] | None:
    path = _state_cache_path(cache_dir, gas, temperature_k, pressure_hpa)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return None
    return _valid_cached_rows(
        payload,
        signature=signature,
        gas=gas,
        temperature_k=temperature_k,
        pressure_hpa=pressure_hpa,
        wavelengths=wavelengths,
    )


def _write_state_checkpoint(
    cache_dir: Path,
    *,
    signature: str,
    gas: str,
    temperature_k: float,
    pressure_hpa: float,
    rows: list[dict],
) -> Path:
    """Atomically persist one completed H2O/O2 state."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = _state_cache_path(cache_dir, gas, temperature_k, pressure_hpa)
    payload = {
        "format": STATE_CACHE_FORMAT,
        "signature": signature,
        "gas": gas,
        "temperature_k": float(temperature_k),
        "pressure_hpa": float(pressure_hpa),
        "rows": rows,
    }
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)
    return path


def _load_o3_xsc(path: Path, min_wavelength_nm: float, max_wavelength_nm: float) -> tuple[np.ndarray, dict[float, np.ndarray]]:
    """Load the Serdyuchenko–Gorshelev O3 cross-section matrix.

    Expected columns: wavelength_nm followed by cross sections at
    293,283,...,193 K in cm^2/molecule. Header/comment lines are ignored.
    """
    rows=[]
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            s=line.strip()
            if not s or not (s[0].isdigit() or s[0] in "+-"):
                continue
            parts=s.split()
            if len(parts) < 12:
                continue
            try:
                vals=[float(x) for x in parts[:12]]
            except ValueError:
                continue
            rows.append(vals)
    if not rows:
        raise SystemExit(f"No numeric O3 XSC rows found in {path}")
    arr=np.asarray(rows,float)
    wl=arr[:,0]
    temps=[293.,283.,273.,263.,253.,243.,233.,223.,213.,203.,193.]
    xsc={t:arr[:,i+1] for i,t in enumerate(temps)}
    good=(wl>=min_wavelength_nm)&(wl<=max_wavelength_nm)
    if good.sum() < 1000:
        raise SystemExit(f"O3 XSC does not adequately cover {min_wavelength_nm:g}–{max_wavelength_nm:g} nm")
    if not np.isfinite(arr[good,1:]).all() or (arr[good,1:]<0).any():
        raise SystemExit(f"O3 XSC contains non-finite/negative values in {min_wavelength_nm:g}–{max_wavelength_nm:g} nm")
    return wl, xsc


def _o3_sigma_band(wl_grid: np.ndarray, xsc_by_temp: dict[float,np.ndarray], temperature_k: float, center_nm: float) -> tuple[float,str]:
    temps=np.array(sorted(xsc_by_temp),float)
    t=float(temperature_k)
    # V8.4.5 is fail-closed: do not extrapolate beyond the measured 193–293 K range.
    if t < temps.min() or t > temps.max():
        raise SystemExit(f"Requested O3 LUT temperature {t:g} K is outside measured Serdyuchenko range 193–293 K")
    lo=np.searchsorted(temps,t,side="right")-1
    hi=np.searchsorted(temps,t,side="left")
    lo=max(0,min(lo,len(temps)-1)); hi=max(0,min(hi,len(temps)-1))
    if lo==hi or np.isclose(temps[lo],temps[hi]):
        sigma=xsc_by_temp[float(temps[lo])]
        provenance=f"SERDYUCHENKO_GORSHELEV_XSC_{temps[lo]:g}K"
    else:
        t0,t1=temps[lo],temps[hi]
        w=(t-t0)/(t1-t0)
        sigma=(1-w)*xsc_by_temp[float(t0)] + w*xsc_by_temp[float(t1)]
        provenance=f"SERDYUCHENKO_GORSHELEV_XSC_LINEAR_T_{t0:g}-{t1:g}K"
    band=(wl_grid>=center_nm-12.5)&(wl_grid<=center_nm+12.5)
    if band.sum()<2:
        raise SystemExit(f"O3 XSC band {center_nm:g} nm not covered")
    # Mean in wavelength space over the same 25-nm diagnostic band used by Firecloud.
    x=wl_grid[band]; y=sigma[band]
    area=float(np.trapezoid(y,x)) if hasattr(np,"trapezoid") else float(np.trapz(y,x))
    return area/float(x[-1]-x[0]), provenance


def main():
    args=parse_args()
    DB=Path(args.db).expanduser(); DB.mkdir(parents=True,exist_ok=True)
    h2o_table=args.h2o_table; o2_table=args.o2_table
    missing=[]
    for gas,table in (("H2O",h2o_table),("O2",o2_table)):
        for suffix in (".data",".header"):
            if not (DB/f"{table}{suffix}").is_file():
                missing.append(f"{gas}:{table}{suffix}")
    o3_path=DB/args.o3_xsc
    if not o3_path.is_file():
        missing.append(f"O3_XSC:{o3_path.name}")
    if missing:
        raise SystemExit("Missing local spectroscopy inputs: "+", ".join(missing))

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            import hapi
            from hapi import db_begin, absorptionCoefficient_Voigt
    except Exception as exc:
        raise SystemExit(f"HAPI unavailable for H2O/O2 build: {exc}")

    temps=[float(x) for x in args.temperatures.split(",") if x.strip()]
    pressures=[float(x) for x in args.pressures_hpa.split(",") if x.strip()]
    wavelengths=sorted({float(x) for x in args.wavelengths.split(",") if x.strip()})
    if not temps or not pressures: raise SystemExit("Temperature and pressure grids must not be empty.")
    if not wavelengths: raise SystemExit("At least one wavelength is required.")
    if any(w < 500.0 or w > 900.0 for w in wavelengths):
        raise SystemExit("Wavelengths must stay inside the supported 500–900 nm diagnostic range.")
    if args.wavenumber_step<=0: raise SystemExit("--wavenumber-step must be positive.")
    if min(temps)<193 or max(temps)>293:
        raise SystemExit("Hybrid V8.4.5 temperature grid must stay inside measured O3 XSC range 193–293 K.")

    requested_min=min(wavelengths)-12.5
    requested_max=max(wavelengths)+12.5
    wl_o3,xsc_o3=_load_o3_xsc(o3_path, requested_min, requested_max)
    db_begin(str(DB))
    input_fingerprints = {
        "h2o_data": _file_fingerprint(DB / f"{h2o_table}.data"),
        "h2o_header": _file_fingerprint(DB / f"{h2o_table}.header"),
        "o2_data": _file_fingerprint(DB / f"{o2_table}.data"),
        "o2_header": _file_fingerprint(DB / f"{o2_table}.header"),
        "o3_xsc": _file_fingerprint(o3_path),
    }
    build_signature = _build_signature(
        temperatures=temps,
        pressures=pressures,
        wavelengths=wavelengths,
        wavenumber_step=args.wavenumber_step,
        h2o_table=h2o_table,
        o2_table=o2_table,
        input_fingerprints=input_fingerprints,
        hapi_version=str(getattr(hapi, "__version__", "unknown")),
    )
    state_cache_dir = DB / STATE_CACHE_DIRNAME
    state_cache_dir.mkdir(parents=True, exist_ok=True)
    rows=[]
    # V8.4.16 performance path: HAPI is expensive mainly per Voigt call.
    # Build one full requested-range spectrum for each (gas,T,P), then integrate
    # every requested diagnostic band from that shared spectrum.
    full_nu_min=1e7/requested_max
    full_nu_max=1e7/requested_min
    band_defs=[]
    for wl in wavelengths:
        lo_nm,hi_nm=wl-12.5,wl+12.5
        band_defs.append((wl,1e7/hi_nm,1e7/lo_nm))

    total_states=2*len(temps)*len(pressures)
    state_index=0
    for gas,table in (("H2O",h2o_table),("O2",o2_table)):
        for T in temps:
            for ph in pressures:
                state_index += 1
                p_atm=ph/1013.25
                cached_rows = _load_state_checkpoint(
                    state_cache_dir,
                    signature=build_signature,
                    gas=gas,
                    temperature_k=T,
                    pressure_hpa=ph,
                    wavelengths=wavelengths,
                )
                if cached_rows is not None:
                    rows.extend(cached_rows)
                    print(
                        f"VOIGT_STATE_CACHE_HIT {state_index}/{total_states} "
                        f"gas={gas} T={T:g}K P={ph:g}hPa rows={len(cached_rows)}",
                        flush=True,
                    )
                    continue
                print(f"VOIGT_STATE {state_index}/{total_states} gas={gas} T={T:g}K P={ph:g}hPa", flush=True)
                try:
                    nu,k=absorptionCoefficient_Voigt(
                        SourceTables=table,
                        Environment={"p":p_atm,"T":T},
                        WavenumberRange=[full_nu_min,full_nu_max],
                        WavenumberStep=args.wavenumber_step,
                        HITRAN_units=True,
                    )
                except Exception as exc:
                    raise SystemExit(f"Cannot calculate {gas} from local table {table}: {exc}")
                nu=np.asarray(nu,float); k=np.asarray(k,float)
                finite=np.isfinite(nu)&np.isfinite(k)
                if finite.sum()<2:
                    raise SystemExit(f"No finite spectroscopy for {gas} at T={T:g} K P={ph:g} hPa")
                nuf=nu[finite]; kf=k[finite]
                state_rows = []
                for wl,nu_min,nu_max in band_defs:
                    band=(nuf>=nu_min)&(nuf<=nu_max)
                    if band.sum()<2:
                        raise SystemExit(f"No finite spectroscopy for {gas} {wl:g} nm at T={T:g} K P={ph:g} hPa")
                    xb=nuf[band]; yb=kf[band]
                    area=float(np.trapezoid(yb,xb)) if hasattr(np,"trapezoid") else float(np.trapz(yb,xb))
                    sigma=area/float(xb[-1]-xb[0])
                    state_rows.append({
                        "wavelength_nm":wl,"gas":gas,"sigma_cm2_molecule":sigma,
                        "temperature_k":T,"pressure_hpa":ph,
                        "spectroscopy_source":"HITRAN_HAPI_VOIGT_LOCAL",
                        "source_table":table,"band_half_width_nm":12.5,
                        "wavenumber_step_cm-1":args.wavenumber_step,
                    })
                _write_state_checkpoint(
                    state_cache_dir,
                    signature=build_signature,
                    gas=gas,
                    temperature_k=T,
                    pressure_hpa=ph,
                    rows=state_rows,
                )
                rows.extend(state_rows)

    # O3 uses measured temperature-dependent broadband cross sections, not a
    # fictitious visible line list. Cross section itself is pressure-independent;
    # duplicate over the pressure grid so the existing runtime lookup contract stays uniform.
    for T in temps:
        for ph in pressures:
            for wl in wavelengths:
                sigma,prov=_o3_sigma_band(wl_o3,xsc_o3,T,wl)
                rows.append({
                    "wavelength_nm":wl,"gas":"O3","sigma_cm2_molecule":sigma,
                    "temperature_k":T,"pressure_hpa":ph,
                    "spectroscopy_source":prov,
                    "source_table":o3_path.name,"band_half_width_nm":12.5,
                    "wavenumber_step_cm-1":np.nan,
                })

    out=pd.DataFrame(rows)
    expected=3*len(temps)*len(pressures)*len(wavelengths)
    if len(out)!=expected: raise SystemExit(f"LUT row count mismatch: got {len(out)}, expected {expected}")
    sig=pd.to_numeric(out["sigma_cm2_molecule"],errors="coerce")
    if not (np.isfinite(sig)&(sig>=0)).all(): raise SystemExit("LUT contains non-finite/negative cross-sections")
    path=DB/"firecloud_600_750nm_band_coefficients.csv"; out.to_csv(path,index=False)
    sha256=hashlib.sha256(path.read_bytes()).hexdigest()
    manifest={
        "format":"Taiwan Firecloud Hybrid Gas Spectroscopy diagnostic-band LUT",
        "builder_optimization":"single full-range Voigt spectrum per gas/T/P; requested bands integrated from shared spectrum",
        "state_checkpoint_resume": {
            "format": STATE_CACHE_FORMAT,
            "signature": build_signature,
            "directory": STATE_CACHE_DIRNAME,
            "scope": "H2O/O2 completed temperature-pressure states; checkpoints are build-only and not promoted to runtime",
        },
        "version":"PhysicsCore-V1.0-R4.8",
        "coefficient_file":path.name,"sha256":sha256,"rows":int(len(out)),
        "gases":["H2O","O3","O2"],"wavelengths_nm":[int(w) if float(w).is_integer() else float(w) for w in wavelengths],
        "temperatures_k":temps,"pressures_hpa":pressures,"band_half_width_nm":12.5,
        "spectroscopy_sources":{
            "H2O":"HITRAN HAPI Voigt local line list",
            "O2":"HITRAN HAPI Voigt local line list",
            "O3":"Serdyuchenko-Gorshelev temperature-dependent absorption cross sections (213–1100 nm)",
        },
        "o3_temperature_policy":"linear interpolation only within measured 193–293 K; no extrapolation",
        "note":"No raw HITRAN transition data or Serdyuchenko source spectra are redistributed by Taiwan Firecloud; this manifest describes a locally generated derived Runtime LUT.",
    }
    (DB/"firecloud_600_750nm_band_coefficients.manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Wrote {path} ({len(out)} rows)")
    print(f"SHA256 {sha256}")
    print("HYBRID_GAS_SPECTROSCOPY_READY_INPUTS")

if __name__=="__main__":
    main()
