import math
import pandas as pd

import firecloud
from firecloud.viewing_spectral import (
    _integrate_view_aerosol,
    _integrate_view_aerosol_prepared,
    _prepare_aerosol_numeric_route_context,
    _route_group_map,
)


def _route_rows():
    rows=[]
    for d in (0.0,10.0,20.0):
        rows.append({
            "time":"2026-09-13T10:00:00+00:00",
            "solar_altitude_deg":-2.0,
            "direction_offset_deg":0.0,
            "distance_km":d,
            "spectral_aod_temporal_evidence_state":"EXACT_VALID_TIME",
            "aod550":0.20,
            "aod575":0.18,
            "aod600":0.16,
            "aod650":0.13,
            "aod700":0.11,
            "aod750":0.09,
            "cams_aerext532_m1_1000hPa":1.0e-5,
            "cams_geopotential_height_m_1000hPa":100.0,
            "cams_aerext532_m1_900hPa":8.0e-6,
            "cams_geopotential_height_m_900hPa":1500.0,
            "cams_aerext532_m1_700hPa":4.0e-6,
            "cams_geopotential_height_m_700hPa":3500.0,
            "cams_aerext532_m1_500hPa":2.0e-6,
            "cams_geopotential_height_m_500hPa":6000.0,
        })
    return pd.DataFrame(rows)


def _target():
    return pd.Series({
        "time":"2026-09-13T10:00:00+00:00",
        "solar_altitude_deg":-2.0,
        "direction_offset_deg":0.0,
        "target_distance_km":20.0,
        "target_base_km":4.0,
        "target_top_km":5.0,
    })


def test_version_contract():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.2"


def test_prepared_aerosol_integrator_is_exact_equivalent():
    route=_route_rows()
    groups=_route_group_map(route)
    key=("2026-09-13T10:00:00+00:00",-2.0,0.0)
    prepared=_prepare_aerosol_numeric_route_context(groups)[key]
    legacy=_integrate_view_aerosol(_target(),groups[key],6371.0,lowest_endpoint_tolerance_km=0.05)
    optimized=_integrate_view_aerosol_prepared(_target(),prepared,6371.0,lowest_endpoint_tolerance_km=0.05)
    assert legacy == optimized


def test_prepared_aerosol_context_preserves_temporal_missing_semantics():
    route=_route_rows()
    route.loc[route["distance_km"].eq(10.0),"spectral_aod_temporal_evidence_state"]="MISSING"
    groups=_route_group_map(route)
    key=("2026-09-13T10:00:00+00:00",-2.0,0.0)
    prepared=_prepare_aerosol_numeric_route_context(groups)[key]
    legacy=_integrate_view_aerosol(_target(),groups[key],6371.0,lowest_endpoint_tolerance_km=0.05)
    optimized=_integrate_view_aerosol_prepared(_target(),prepared,6371.0,lowest_endpoint_tolerance_km=0.05)
    assert legacy == optimized
    assert optimized[1] == "VIEW_AEROSOL_3D_PARTIAL"
    assert optimized[3]["temporal_missing_segment_count"] == 1


def test_prepared_aerosol_context_preserves_endpoint_snap_semantics():
    route=_route_rows()
    # Put the lowest native level just above the observer LOS; tolerance allows
    # the same explicit lowest-native endpoint snap as the legacy integrator.
    route["cams_geopotential_height_m_1000hPa"]=20.0
    groups=_route_group_map(route)
    key=("2026-09-13T10:00:00+00:00",-2.0,0.0)
    prepared=_prepare_aerosol_numeric_route_context(groups)[key]
    legacy=_integrate_view_aerosol(_target(),groups[key],6371.0,lowest_endpoint_tolerance_km=0.05)
    optimized=_integrate_view_aerosol_prepared(_target(),prepared,6371.0,lowest_endpoint_tolerance_km=0.05)
    assert legacy == optimized
