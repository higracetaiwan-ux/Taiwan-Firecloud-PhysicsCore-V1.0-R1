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
    rec = {"dummy": True}
    prepared = {0.0: {"distances": np.array([0.0, 1.0, 2.0]), "profiles": {0.0: rec, 1.0: rec, 2.0: rec}}}
    lut = {
        (gas, wl): (np.array([280.0]), np.array([900.0]), np.array([math.log(900.0)]), np.array([1e-30]))
        for gas in ("O2", "H2O", "O3") for wl in (550, 575, 600, 650, 700, 750)
    }
    return SimpleNamespace(valid=True, prepared_profile=prepared, lut=lut)


def _state():
    return {
        "temperature_k": 285.0,
        "pressure_hpa": 850.0,
        "o2_mole_fraction": 0.20946,
        "h2o_mole_fraction": 0.01,
        "o3_mole_fraction": 8e-8,
    }


def _sigma(_lut, gas, wl, tk, ph):
    factor = {"O2": 1.0, "H2O": 2.0, "O3": 3.0}[gas]
    return factor * int(wl) * 1e-35


def test_version_contract_r5741341091():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.18"


def test_preseeded_viewing_cache_reports_handoff_hits_without_changing_output(monkeypatch):
    monkeypatch.setattr(tg, "_interp_fast_profile_state_lowest_boundary", lambda *_a, **_k: dict(_state()))
    ctx = _ctx(); sig = "fixture-lut"
    monkeypatch.setattr(tg, "_sigma_fast", _sigma)
    baseline = tg._observer_gas_species_path(_target(), ctx, 6371.0)

    cache = {}
    for gas in ("O2", "H2O", "O3"):
        for wl in tg.SIX_BAND_WAVELENGTHS_NM:
            cache[(sig, gas, int(wl), 285.0, 850.0)] = _sigma(ctx.lut, gas, int(wl), 285.0, 850.0)
    initial_keys = frozenset(cache.keys())
    telemetry = {}

    def boom(*_a, **_k):
        raise AssertionError("pre-seeded Viewing cache should serve every exact Glow spectroscopy lookup")
    monkeypatch.setattr(tg, "_sigma_fast", boom)
    cached = tg._observer_gas_species_path(
        _target(), ctx, 6371.0,
        sigma_cache=cache,
        lut_signature=sig,
        sigma_cache_telemetry=telemetry,
        sigma_cache_initial_keys=initial_keys,
    )
    assert cached == baseline
    assert telemetry["lookup_count"] == 2 * 6 * 3
    assert telemetry["hit_count"] == 2 * 6 * 3
    assert telemetry["handoff_hit_count"] == 2 * 6 * 3
    assert telemetry["intra_glow_hit_count"] == 0
    assert telemetry["miss_count"] == 0
    assert telemetry.get("uncached_fallback_count", 0) == 0


def test_empty_shared_cache_distinguishes_first_misses_from_intra_glow_hits(monkeypatch):
    monkeypatch.setattr(tg, "_interp_fast_profile_state_lowest_boundary", lambda *_a, **_k: dict(_state()))
    monkeypatch.setattr(tg, "_sigma_fast", _sigma)
    cache = {}; telemetry = {}; initial_keys = frozenset()
    result = tg._observer_gas_species_path(
        _target(), _ctx(), 6371.0,
        sigma_cache=cache,
        lut_signature="fixture-lut",
        sigma_cache_telemetry=telemetry,
        sigma_cache_initial_keys=initial_keys,
    )
    assert result[1] == "GLOW_OBSERVER_GAS_PATH_RESOLVED"
    assert telemetry["lookup_count"] == 2 * 6 * 3
    assert telemetry["miss_count"] == 6 * 3
    assert telemetry["hit_count"] == 6 * 3
    assert telemetry["handoff_hit_count"] == 0
    assert telemetry["intra_glow_hit_count"] == 6 * 3
    assert len(cache) == 6 * 3


def test_missing_signature_counts_uncached_fallback_and_preserves_cache(monkeypatch):
    monkeypatch.setattr(tg, "_interp_fast_profile_state_lowest_boundary", lambda *_a, **_k: dict(_state()))
    monkeypatch.setattr(tg, "_sigma_fast", _sigma)
    cache = {}; telemetry = {}
    result = tg._observer_gas_species_path(
        _target(), _ctx(), 6371.0,
        sigma_cache=cache,
        lut_signature=None,
        sigma_cache_telemetry=telemetry,
        sigma_cache_initial_keys=frozenset(),
    )
    assert result[1] == "GLOW_OBSERVER_GAS_PATH_RESOLVED"
    assert telemetry["uncached_fallback_count"] == 2 * 6 * 3
    assert telemetry.get("lookup_count", 0) == 0
    assert cache == {}
