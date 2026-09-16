import math
from types import SimpleNamespace

import numpy as np
import pandas as pd

import firecloud
from firecloud import twilight_glow as tg
from firecloud.viewing_spectral import prepare_viewing_spectral_runtime_context


def _profiles():
    rows=[]
    for distance in (0.0, 5.0, 10.0):
        for z,t,p,state in (
            (0.02, 299.0, 1005.0, 'READY'),
            (0.50, 295.0, 950.0, ''),
            (1.00, 291.0, 900.0, ''),
            (2.00, 285.0, 800.0, ''),
        ):
            rows.append({
                'time':'2026-09-14 05:30:00+08:00',
                'solar_altitude_deg':-2.0,
                'direction_offset_deg':0.0,
                'distance_km':distance,
                'altitude_agl_km':z,
                'temperature_k':t,
                'pressure_hpa':p,
                'o2_mole_fraction':0.2095,
                'h2o_mole_fraction':0.01,
                'o3_mole_fraction':5e-8,
                'near_surface_boundary_state':state,
            })
    return pd.DataFrame(rows)


def _assert_route_exact(a,b):
    assert set(a)==set(b)
    for k in a:
        assert np.array_equal(a[k]['distances'], b[k]['distances'], equal_nan=True)
        assert set(a[k]['profiles'])==set(b[k]['profiles'])
        for d in a[k]['profiles']:
            ar=a[k]['profiles'][d]; br=b[k]['profiles'][d]
            for field in ('z','temperature_k','pressure_hpa'):
                assert np.array_equal(ar[field], br[field], equal_nan=True), (k,d,field)
            for field in ('actual_lo','anchor_lo','pressure_lo'):
                assert ar[field]==br[field], (k,d,field,ar[field],br[field])


def test_version_contract():
    assert firecloud.__version__ == '1.0.0-R5.7.41.3.4.10.20'


def test_shared_viewing_gas_context_rebuilds_exact_glow_molecular_routes():
    gp=_profiles()
    ctx=prepare_viewing_spectral_runtime_context(pd.DataFrame(),pd.DataFrame(),pd.DataFrame(),gp)
    shared=tg._prepare_glow_molecular_numeric_routes_from_viewing_context(ctx)
    legacy=tg._prepare_glow_molecular_numeric_routes(gp)
    _assert_route_exact(legacy,shared)
    assert all(v['contract']=='R574134108_VIEWING_GLOW_MOLECULAR_CONTEXT_HANDOFF' for v in shared.values())


def test_shared_handoff_requires_all_gas_routes_valid_and_falls_back():
    gp=_profiles()
    ctx=prepare_viewing_spectral_runtime_context(pd.DataFrame(),pd.DataFrame(),pd.DataFrame(),gp)
    key=next(iter(ctx['gas_contexts']))
    ctx['gas_contexts'][key]=SimpleNamespace(valid=False, prepared_profile={})
    assert tg._prepare_glow_molecular_numeric_routes_from_viewing_context(ctx)=={}
    routes,source=tg._select_glow_molecular_numeric_routes(gp,ctx)
    assert source=='GLOW_LOCAL_PREPARE_FALLBACK'
    _assert_route_exact(tg._prepare_glow_molecular_numeric_routes(gp),routes)


def test_selector_prefers_shared_context_when_complete(monkeypatch):
    gp=_profiles()
    ctx=prepare_viewing_spectral_runtime_context(pd.DataFrame(),pd.DataFrame(),pd.DataFrame(),gp)
    def _boom(*args,**kwargs):
        raise AssertionError('legacy molecular prep must not run when shared handoff is complete')
    monkeypatch.setattr(tg,'_prepare_glow_molecular_numeric_routes',_boom)
    routes,source=tg._select_glow_molecular_numeric_routes(gp,ctx)
    assert source=='SHARED_VIEWING_GAS_CONTEXT'
    assert routes
