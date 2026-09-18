import math
from types import SimpleNamespace

import numpy as np
import pandas as pd

import firecloud
import firecloud.viewing_spectral as vs


def _target(distance=2.0):
    return pd.Series({
        "direction_offset_deg": 0.0,
        "target_distance_km": distance,
        "target_base_km": 1.0,
        "target_top_km": 1.0,
    })


def _ctx():
    rec={"dummy": True}
    prepared={0.0:{"distances":np.array([0.0,1.0,2.0]),"profiles":{0.0:rec,1.0:rec,2.0:rec}}}
    lut={(gas,wl):(np.array([280.0]),np.array([900.0]),np.array([math.log(900.0)]),np.array([1e-30]))
         for gas in ("O2","H2O","O3") for wl in (550,575,600,650,700,750)}
    return SimpleNamespace(valid=True, prepared_profile=prepared, lut=lut)


def test_version():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.30.1.1"


def test_lut_content_signature_is_content_scoped():
    a=_ctx().lut
    b={k:tuple(np.array(x,copy=True) for x in rec) for k,rec in a.items()}
    assert vs._gas_lut_content_signature(a) == vs._gas_lut_content_signature(b)
    b[("O3",550)][3][0] *= 2.0
    assert vs._gas_lut_content_signature(a) != vs._gas_lut_content_signature(b)


def test_sigma_state_memo_is_exact_and_reuses_same_state(monkeypatch):
    state={
        "temperature_k":285.0,
        "pressure_hpa":850.0,
        "o2_mole_fraction":0.20946,
        "h2o_mole_fraction":0.01,
        "o3_mole_fraction":8e-8,
    }
    monkeypatch.setattr(vs,"_interp_fast_profile_state",lambda *_a,**_k:dict(state))
    calls=[]
    def fake_sigma(_lut,gas,wl,tk,ph):
        calls.append((gas,int(wl),float(tk),float(ph)))
        factor={"O2":1.0,"H2O":2.0,"O3":3.0}[gas]
        return factor*int(wl)*1e-35
    monkeypatch.setattr(vs,"_sigma_fast",fake_sigma)
    ctx=_ctx(); rows=pd.DataFrame([{"x":1}])

    legacy=vs._integrate_view_gas(_target(),rows,6371.0,prepared_context=ctx)
    legacy_calls=len(calls)
    assert legacy_calls == 2*6*3

    calls.clear(); cache={}; sig=vs._gas_lut_content_signature(ctx.lut)
    cached1=vs._integrate_view_gas(_target(),rows,6371.0,prepared_context=ctx,sigma_cache=cache,lut_signature=sig)
    cached2=vs._integrate_view_gas(_target(),rows,6371.0,prepared_context=ctx,sigma_cache=cache,lut_signature=sig)

    assert cached1 == legacy
    assert cached2 == legacy
    assert len(calls) == 6*3
    assert len(cache) == 6*3
