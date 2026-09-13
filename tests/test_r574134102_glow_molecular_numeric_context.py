import math

import pandas as pd

import firecloud
from firecloud import twilight_glow as tg


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
                'time':'2026-09-13 18:00:00+08:00',
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


def _target(base=0.0, top=0.2):
    return pd.Series({
        'target_distance_km':10.0,
        'target_base_km':base,
        'target_top_km':top,
        'direction_offset_deg':0.0,
    })


def _diag_equal(a,b):
    assert a.keys()==b.keys()
    for k in a:
        av,bv=a[k],b[k]
        if isinstance(av,float) and isinstance(bv,float) and math.isnan(av) and math.isnan(bv):
            continue
        assert av==bv, (k,av,bv)


def test_version_contract():
    assert firecloud.__version__ == '1.0.0-R5.7.41.3.4.10.2'


def test_prepared_rayleigh_exact_equivalent():
    gp=_profiles(); key=('2026-09-13 18:00:00+08:00',-2.0,0.0)
    legacy=tg._gas_profile_index(gp)[key]
    prepared=tg._prepare_glow_molecular_numeric_routes(gp)[key]
    assert tg._rayleigh_observer_path(_target(),legacy,6371.0) == tg._rayleigh_observer_path_prepared(_target(),prepared,6371.0)


def test_prepared_local_state_exact_equivalent():
    gp=_profiles(); key=('2026-09-13 18:00:00+08:00',-2.0,0.0)
    legacy=tg._gas_profile_index(gp)[key]
    prepared=tg._prepare_glow_molecular_numeric_routes(gp)[key]
    assert tg._local_molecular_state(_target(0.4,0.6),legacy) == tg._local_molecular_state_prepared(_target(0.4,0.6),prepared)


def test_prepared_boundary_diagnostics_exact_equivalent():
    gp=_profiles(); key=('2026-09-13 18:00:00+08:00',-2.0,0.0)
    legacy=tg._gas_profile_index(gp)[key]
    prepared=tg._prepare_glow_molecular_numeric_routes(gp)[key]
    _diag_equal(
        tg._molecular_boundary_diagnostics(_target(),legacy,6371.0),
        tg._molecular_boundary_diagnostics_prepared(_target(),prepared,6371.0),
    )


def test_boundary_route_context_keeps_native_lowest_anchor_metadata():
    gp=_profiles(); key=('2026-09-13 18:00:00+08:00',-2.0,0.0)
    route=tg._prepare_glow_molecular_numeric_routes(gp)[key]
    assert route['contract']=='R574134102_GLOW_MOLECULAR_NUMERIC_ROUTE_CONTEXT'
    rec=route['profiles'][0.0]
    assert rec['actual_lo']==0.02
    assert rec['anchor_lo']==0.02
    assert rec['pressure_lo']==0.5
