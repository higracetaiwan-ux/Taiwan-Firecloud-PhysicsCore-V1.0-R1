import math
from types import SimpleNamespace

import numpy as np
import pandas as pd

import firecloud
from firecloud import twilight_glow as tg


def _target(distance=2.0):
    return pd.Series({
        "direction_offset_deg": 0.0,
        "target_distance_km": distance,
        "target_base_km": 1.0,
        "target_top_km": 1.5,
    })


def _ctx():
    rec={"dummy": True}
    prepared={0.0:{"distances":np.array([0.0,1.0,2.0]),"profiles":{0.0:rec,1.0:rec,2.0:rec}}}
    lut={(gas,wl):(np.array([280.0]),np.array([900.0]),np.array([math.log(900.0)]),np.array([1e-30]))
         for gas in ("O2","H2O","O3") for wl in (550,575,600,650,700,750)}
    return SimpleNamespace(valid=True, prepared_profile=prepared, lut=lut)


def _state():
    return {
        "temperature_k":285.0,
        "pressure_hpa":850.0,
        "o2_mole_fraction":0.20946,
        "h2o_mole_fraction":0.01,
        "o3_mole_fraction":8e-8,
    }


def test_version_contract():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.30.15"


def test_glow_sigma_cache_handoff_is_exact_and_reuses_same_state(monkeypatch):
    monkeypatch.setattr(tg,"_interp_fast_profile_state_lowest_boundary",lambda *_a,**_k:dict(_state()))
    calls=[]
    def fake_sigma(_lut,gas,wl,tk,ph):
        calls.append((gas,int(wl),float(tk),float(ph)))
        factor={"O2":1.0,"H2O":2.0,"O3":3.0}[gas]
        return factor*int(wl)*1e-35
    monkeypatch.setattr(tg,"_sigma_fast",fake_sigma)
    ctx=_ctx()
    legacy=tg._observer_gas_species_path(_target(),ctx,6371.0)
    assert len(calls)==2*6*3

    calls.clear(); cache={}; sig="fixture-lut"
    cached1=tg._observer_gas_species_path(_target(),ctx,6371.0,sigma_cache=cache,lut_signature=sig)
    cached2=tg._observer_gas_species_path(_target(),ctx,6371.0,sigma_cache=cache,lut_signature=sig)
    assert cached1==legacy
    assert cached2==legacy
    assert len(calls)==6*3
    assert len(cache)==6*3


def test_preseeded_shared_sigma_cache_can_serve_glow_without_sigma_recompute(monkeypatch):
    monkeypatch.setattr(tg,"_interp_fast_profile_state_lowest_boundary",lambda *_a,**_k:dict(_state()))
    ctx=_ctx(); sig="fixture-lut"
    def fake_sigma(_lut,gas,wl,tk,ph):
        factor={"O2":1.0,"H2O":2.0,"O3":3.0}[gas]
        return factor*int(wl)*1e-35
    monkeypatch.setattr(tg,"_sigma_fast",fake_sigma)
    baseline=tg._observer_gas_species_path(_target(),ctx,6371.0)
    cache={}
    for gas in ("O2","H2O","O3"):
        for wl in tg.SIX_BAND_WAVELENGTHS_NM:
            cache[(sig,gas,int(wl),285.0,850.0)]=fake_sigma(ctx.lut,gas,int(wl),285.0,850.0)
    def boom(*_a,**_k):
        raise AssertionError("_sigma_fast must not run when the exact spectroscopy state is already shared")
    monkeypatch.setattr(tg,"_sigma_fast",boom)
    cached=tg._observer_gas_species_path(_target(),ctx,6371.0,sigma_cache=cache,lut_signature=sig)
    assert cached==baseline


def test_missing_signature_preserves_legacy_fallback(monkeypatch):
    monkeypatch.setattr(tg,"_interp_fast_profile_state_lowest_boundary",lambda *_a,**_k:dict(_state()))
    calls=[]
    def fake_sigma(_lut,gas,wl,tk,ph):
        calls.append((gas,int(wl),float(tk),float(ph)))
        return 1e-32
    monkeypatch.setattr(tg,"_sigma_fast",fake_sigma)
    cache={}
    tg._observer_gas_species_path(_target(),_ctx(),6371.0,sigma_cache=cache,lut_signature=None)
    assert len(calls)==2*6*3
    assert cache=={}
