import math
import pandas as pd

from firecloud.providers.cams_native import (
    build_ads_aerosol_scattering_properties_request,
    AEROSOL_SCATTERING_AOD_VARIABLES,
    AEROSOL_SCATTERING_SSA_VARIABLES,
    AEROSOL_SCATTERING_G_VARIABLES,
)
from firecloud.twilight_glow import (
    build_twilight_glow_aerosol_scattering,
    heney_greenstein_phase_function_sr,
    _bounded_property_at_wavelength,
)


def _detail():
    row={
        "time":"2026-09-09T10:00:00+00:00","solar_altitude_deg":-2.0,"solar_azimuth_deg":270.0,
        "glow_volume_id":"glowvol::x","reference_receiver_id":"redref::x","direction_offset_deg":0.0,
        "distance_km":40.0,"scatter_altitude_km":5.0,"target_lat":23.0,"target_lon":121.0,
        "scattering_angle_deg":70.0,
    }
    for w in (550,575,600,650,700,750):
        row[f"glow_sun_incident_relative_irradiance_{w}nm"]=0.4
        row[f"glow_observer_transmission_{w}nm"]=0.7
        row[f"glow_single_scattering_source_proxy_{w}nm"]=1e-8
    return pd.DataFrame([row])


def _cams(aod532=0.2):
    row={
        "time":"2026-09-09T10:00:00+00:00","solar_altitude_deg":-2.0,"direction_offset_deg":0.0,
        "distance_km":40.0,"point_id":"p","cams_aerosol_scattering_property_source":"CAMS_ADS",
        "cams_aerext532_m1_700hPa":1.0e-5,"cams_geopotential_height_m_700hPa":4000.0,
        "cams_aerext532_m1_500hPa":5.0e-6,"cams_geopotential_height_m_500hPa":6000.0,
        "aod532":aod532,"aod550":0.19,"aod645":0.15,"aod670":0.14,"aod800":0.10,
        "ssa550":0.92,"ssa645":0.91,"ssa670":0.90,"ssa800":0.88,
        "asymmetry550":0.68,"asymmetry645":0.69,"asymmetry670":0.70,"asymmetry800":0.72,
    }
    return pd.DataFrame([row])


def test_r5735_ads_request_uses_native_aod_ssa_and_asymmetry():
    points=[{"point_id":"p","distance_km":0,"direction_offset_deg":0,"lat":23,"lon":121}]
    request,meta=build_ads_aerosol_scattering_properties_request(points,pd.Timestamp("2026-09-09T10:00:00Z").to_pydatetime())
    variables=set(request["variable"])
    assert set(AEROSOL_SCATTERING_AOD_VARIABLES.values()) <= variables
    assert set(AEROSOL_SCATTERING_SSA_VARIABLES.values()) <= variables
    assert set(AEROSOL_SCATTERING_G_VARIABLES.values()) <= variables
    assert meta["request_role"] == "AEROSOL_SCATTERING_COLUMN_PROPERTIES"


def test_r5735_hg_is_normalized_formula_value():
    g=0.7; theta=60.0
    got=heney_greenstein_phase_function_sr(theta,g)
    expected=(1-g*g)/(4*math.pi*(1+g*g-2*g*math.cos(math.radians(theta)))**1.5)
    assert abs(got-expected) < 1e-15


def test_r5735_bounded_properties_never_extrapolate():
    r=pd.Series({"ssa550":0.9,"ssa645":0.8,"ssa670":0.75,"ssa800":0.7})
    v,p=_bounded_property_at_wavelength(r,"ssa",600)
    assert 0.8 < v < 0.9 and p == "BOUNDED_NATIVE_550_645NM"
    v,p=_bounded_property_at_wavelength(r,"ssa",900)
    assert v is None and p == "MISSING_NO_NATIVE_BRACKET"


def test_r5735_aerosol_single_scattering_numeric_closure():
    out=build_twilight_glow_aerosol_scattering(_detail(),_cams())
    assert len(out)==1
    r=out.iloc[0]
    assert r["glow_aerosol_scattering_state"] == "GLOW_AEROSOL_SINGLE_SCATTERING_PROXY_READY"
    for w in (550,575,600,650,700,750):
        beta532=r["aerosol_local_extinction_532_m1"]
        ext=beta532*r[f"aerosol_aod_{w}nm"]/r["aerosol_aod532_anchor"]
        assert abs(r[f"aerosol_extinction_coefficient_m1_{w}nm"]-ext) < 1e-15
        sca=ext*r[f"aerosol_ssa_{w}nm"]
        assert abs(r[f"aerosol_scattering_coefficient_m1_{w}nm"]-sca) < 1e-15
        src=sca*r[f"aerosol_hg_phase_function_sr_{w}nm"]
        assert abs(r[f"aerosol_source_coefficient_m1_sr_{w}nm"]-src) < 1e-15
        proxy=.4*.7*src
        assert abs(r[f"aerosol_single_scattering_source_proxy_{w}nm"]-proxy) < 1e-18
        assert abs(r[f"rayleigh_plus_aerosol_source_proxy_{w}nm"]-(1e-8+proxy)) < 1e-18
        assert "EXTRAP" not in r[f"aerosol_ssa_provenance_{w}nm"]


def test_r5735_aod532_conflict_stays_missing_not_zero():
    out=build_twilight_glow_aerosol_scattering(_detail(),_cams(aod532=0.0))
    r=out.iloc[0]
    assert r["glow_aerosol_scattering_state"] == "GLOW_AEROSOL_SCATTERING_DIRECT_EVIDENCE_CONFLICT"
    for w in (550,575,600,650,700,750):
        assert pd.isna(r[f"aerosol_extinction_coefficient_m1_{w}nm"])
        assert pd.isna(r[f"aerosol_single_scattering_source_proxy_{w}nm"])
        assert r[f"aerosol_band_evidence_state_{w}nm"] == "MISSING"


def test_r5735_analysis_integrity_guards_close_on_valid_aerosol_table():
    from firecloud.case_integrity import build_analysis_integrity_audit
    detail=_detail()
    aero=build_twilight_glow_aerosol_scattering(detail,_cams())
    audit=build_analysis_integrity_audit({
        "v1_twilight_glow_scattering_volume_550_750nm":detail,
        "v1_twilight_glow_aerosol_scattering_550_750nm":aero,
        "twilight_glow_required":True,
        "twilight_glow_aerosol_scattering_phase1_required":True,
    })
    wanted={
        "TWILIGHT_GLOW_AEROSOL_SCATTERING_TARGET_COVERAGE",
        "TWILIGHT_GLOW_AEROSOL_SCATTERING_SCHEMA",
        "TWILIGHT_GLOW_AEROSOL_SCATTERING_NUMERIC_CLOSURE",
        "TWILIGHT_GLOW_AEROSOL_SCATTERING_PROVENANCE",
    }
    got=audit[audit.check_id.isin(wanted)].set_index("check_id")["status"].to_dict()
    assert set(got)==wanted
    assert set(got.values())=={"PASS"}
