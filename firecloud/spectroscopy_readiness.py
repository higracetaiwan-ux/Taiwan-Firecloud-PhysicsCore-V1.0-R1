"""PhysicsCore V1.0-R4.7 six-band spectroscopy readiness diagnostics.

This module never interpolates missing spectroscopy.  It audits the installed
runtime LUT against the frozen 550/575/600/650/700/750 nm gas contract and
reports readiness per gas and wavelength.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

from .contracts import SIX_BAND_WAVELENGTHS_NM

REQ_T=(220.0,250.0,280.0,293.0)
REQ_P=(100.0,300.0,500.0,700.0,900.0,1000.0)
REQ_GASES=("H2O","O2","O3")


def build_six_band_spectroscopy_readiness(runtime_csv: str | Path) -> pd.DataFrame:
    path=Path(runtime_csv)
    rows=[]
    if not path.is_file():
        for gas in REQ_GASES:
            for wl in SIX_BAND_WAVELENGTHS_NM:
                rows.append({"gas":gas,"wavelength_nm":int(wl),"state":"MISSING_RUNTIME_LUT","complete_tp_grid":False,"resolved_state_count":0,"required_state_count":len(REQ_T)*len(REQ_P),"runtime_lut":str(path)})
        return pd.DataFrame(rows)
    try:
        df=pd.read_csv(path)
    except Exception as exc:
        for gas in REQ_GASES:
            for wl in SIX_BAND_WAVELENGTHS_NM:
                rows.append({"gas":gas,"wavelength_nm":int(wl),"state":f"LUT_READ_FAILED:{type(exc).__name__}","complete_tp_grid":False,"resolved_state_count":0,"required_state_count":len(REQ_T)*len(REQ_P),"runtime_lut":str(path)})
        return pd.DataFrame(rows)
    if df.empty:
        return build_six_band_spectroscopy_readiness(path.with_name("__missing__"))
    work=df.copy()
    work["gas"]=work.get("gas",pd.Series(dtype=str)).astype(str).str.upper().str.strip()
    for c in ("wavelength_nm","temperature_k","pressure_hpa","sigma_cm2_molecule"):
        work[c]=pd.to_numeric(work.get(c,np.nan),errors="coerce")
    expected={(t,p) for t in REQ_T for p in REQ_P}
    for gas in REQ_GASES:
        for wl in SIX_BAND_WAVELENGTHS_NM:
            q=work[(work["gas"]==gas)&np.isclose(work["wavelength_nm"],float(wl),equal_nan=False)].copy()
            valid=q[np.isfinite(q["sigma_cm2_molecule"]) & (q["sigma_cm2_molecule"]>=0)]
            states=set(zip(valid["temperature_k"].astype(float),valid["pressure_hpa"].astype(float)))
            complete=expected.issubset(states)
            src=";".join(sorted({str(x) for x in valid.get("spectroscopy_source",pd.Series(dtype=str)).dropna()}))
            rows.append({
                "gas":gas,"wavelength_nm":int(wl),"state":"READY" if complete else ("MISSING_BAND" if q.empty else "INCOMPLETE_TP_GRID"),
                "complete_tp_grid":bool(complete),"resolved_state_count":len(expected & states),"required_state_count":len(expected),
                "spectroscopy_source":src,"runtime_lut":str(path),
                "no_interpolation":True,
            })
    return pd.DataFrame(rows)
