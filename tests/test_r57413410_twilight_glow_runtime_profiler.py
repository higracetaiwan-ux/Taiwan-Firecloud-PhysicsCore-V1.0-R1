import math
from pathlib import Path

import pandas as pd
import firecloud
import firecloud.twilight_glow as glow
from firecloud.contracts import SIX_BAND_WAVELENGTHS_NM

EXPECTED_INTERNAL = {
    "GEOMETRY",
    "TARGETS",
    "OBSERVER_PRECIPITATION",
    "OBSERVER_SPECTRAL_EXTINCTION",
    "LOOKUP_CONTEXT_PREP",
    "VOLUME_ASSEMBLY",
    "SUMMARY",
}

EXPECTED_STAGES = {
    "TWILIGHT_GLOW_COMPONENT_GEOMETRY",
    "TWILIGHT_GLOW_COMPONENT_TARGETS",
    "TWILIGHT_GLOW_COMPONENT_OBSERVER_PRECIPITATION",
    "TWILIGHT_GLOW_COMPONENT_OBSERVER_SPECTRAL_EXTINCTION",
    "TWILIGHT_GLOW_COMPONENT_LOOKUP_CONTEXT_PREP",
    "TWILIGHT_GLOW_COMPONENT_VOLUME_ASSEMBLY",
    "TWILIGHT_GLOW_COMPONENT_SUMMARY",
    "TWILIGHT_GLOW_COMPONENT_PHASE1_EXPORTS",
    "TWILIGHT_GLOW_COMPONENT_AEROSOL_SCATTERING",
    "TWILIGHT_GLOW_COMPONENT_AEROSOL_SUMMARY_ATTACH",
}


def _timeline():
    return pd.DataFrame([{
        "time": "2026-09-13T10:00:00+00:00",
        "solar_altitude_deg": -4.0,
        "solar_azimuth_deg": 270.0,
    }])


def _red_reference(timeline):
    event = timeline.iloc[0]
    row = {
        "time": event["time"],
        "solar_altitude_deg": event["solar_altitude_deg"],
        "reference_receiver_id": "redref::test",
        "direction_offset_deg": 0.0,
        "distance_km": 10.0,
        "sampled_receiver_altitude_km": 4.0,
        "voxel_bottom_km": 3.75,
        "voxel_top_km": 4.25,
        "v1_direct_solar_fraction": 1.0,
        "red_light_path_state": "RED_LIGHT_PATH_FULL",
        "red_light_path_evidence_complete": True,
        "red_light_cloud_evidence_state": "FULL",
        "red_light_aerosol_evidence_state": "FULL_EXACT_VALID_TIME",
        "red_light_gas_evidence_state": "FULL",
        "red_light_precipitation_evidence_state": "FULL",
        "resolved_upstream_cloud_tau": 0.1,
    }
    precip_tau = math.log(2.0) - 0.1 - 0.1 - 0.2 - 0.1
    for wavelength in SIX_BAND_WAVELENGTHS_NM:
        w = int(wavelength)
        row[f"rayleigh_tau_{w}nm"] = 0.1
        row[f"aerosol_tau_{w}nm"] = 0.1
        row[f"gas_tau_{w}nm"] = 0.2
        row[f"gas_tau_o3_{w}nm"] = 0.05
        row[f"tau_precip_{w}nm"] = precip_tau
        row[f"red_light_availability_{w}nm"] = 0.5
    return pd.DataFrame([row])


def _gas_profiles(timeline):
    rows = []
    event = timeline.iloc[0]
    for distance in (0.0, 10.0):
        for altitude, pressure, temperature in (
            (0.0, 1013.25, 288.15),
            (6.0, 472.0, 249.0),
            (15.0, 120.0, 216.0),
        ):
            rows.append({
                "time": event["time"],
                "solar_altitude_deg": event["solar_altitude_deg"],
                "direction_offset_deg": 0.0,
                "distance_km": distance,
                "altitude_agl_km": altitude,
                "temperature_k": temperature,
                "pressure_hpa": pressure,
            })
    return pd.DataFrame(rows)


def _full_observer_rt(targets, *_args, **_kwargs):
    rows = []
    for _, target in targets.iterrows():
        row = {
            "time": target["time"],
            "solar_altitude_deg": target["solar_altitude_deg"],
            "canvas_id": target["canvas_id"],
            "viewing_spectral_status": "VIEW_FULL_SIX_BAND_RT",
            "view_gas_status": "VIEW_GAS_RT_RESOLVED",
            "view_aerosol_status": "VIEW_AEROSOL_3D_RESOLVED",
            "view_cloud_status": "VIEW_CLOUD_PATH_CLEAR",
            "view_precipitation_status": "VIEW_PRECIPITATION_OPTICS_RESOLVED",
        }
        for wavelength in SIX_BAND_WAVELENGTHS_NM:
            w = int(wavelength)
            row[f"view_tau_gas_{w}nm"] = 0.1
            row[f"view_tau_aerosol_{w}nm"] = 0.02
            row[f"view_tau_cloud_{w}nm"] = 0.0
            row[f"view_tau_precip_{w}nm"] = 0.0
            row[f"view_tau_total_{w}nm"] = 0.12
        rows.append(row)
    return pd.DataFrame(rows)


def _call(monkeypatch, stats=None):
    timeline = _timeline()
    monkeypatch.setattr(glow, "_observer_precipitation", lambda *_a, **_k: pd.DataFrame())
    monkeypatch.setattr(glow, "build_viewing_spectral_extinction", _full_observer_rt)
    monkeypatch.setattr(
        glow,
        "_observer_gas_species_path",
        lambda *_a, **_k: (
            {int(w): {"o3": 0.02, "non_o3": 0.08, "total": 0.1} for w in SIX_BAND_WAVELENGTHS_NM},
            "GLOW_OBSERVER_GAS_PATH_RESOLVED",
            1, 1, 10.0,
        ),
    )
    return glow.build_twilight_glow_branch(
        red_light_reference=_red_reference(timeline),
        event_timeline=timeline,
        cloud_layers=pd.DataFrame(),
        target_optics=pd.DataFrame(),
        aerosol_snapshots=pd.DataFrame(),
        gas_profiles=_gas_profiles(timeline),
        route_snapshots=pd.DataFrame(),
        observer_lat_deg=25.04,
        observer_lon_deg=121.52,
        runtime_cache_stats=stats,
    )


def test_version_r57413410():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.1"


def test_glow_internal_profiler_is_output_exact(monkeypatch):
    baseline_detail, baseline_summary = _call(monkeypatch)
    stats = {}
    profiled_detail, profiled_summary = _call(monkeypatch, stats)
    pd.testing.assert_frame_equal(profiled_detail, baseline_detail, check_dtype=True, check_exact=True)
    pd.testing.assert_frame_equal(profiled_summary, baseline_summary, check_dtype=True, check_exact=True)
    seconds = stats.get("component_seconds", {})
    assert set(seconds) == EXPECTED_INTERNAL
    assert all(float(seconds[key]) >= 0.0 for key in EXPECTED_INTERNAL)


def test_model_exports_all_glow_component_stages_as_diagnostic_only():
    model = (Path(__file__).resolve().parents[1] / "firecloud" / "model.py").read_text(encoding="utf-8")
    for stage in EXPECTED_STAGES:
        assert f'"{stage}"' in model
    assert "R57413410_COMPONENT_PROFILE_ONLY" in model
    assert "TWILIGHT_GLOW_INDEPENDENT_BRANCH" in model
