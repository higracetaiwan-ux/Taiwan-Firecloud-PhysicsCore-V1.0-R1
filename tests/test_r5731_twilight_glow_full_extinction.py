from pathlib import Path
import math

import pandas as pd

from firecloud.case_integrity import build_analysis_integrity_audit, build_archive_integrity_audit
from firecloud.contracts import SIX_BAND_WAVELENGTHS_NM
import firecloud.twilight_glow as twilight_glow


def _timeline():
    return pd.DataFrame([{
        "time": "2026-09-09T10:00:00+00:00",
        "solar_altitude_deg": -4.0,
        "solar_azimuth_deg": 270.0,
    }])


def _red_reference(*, cloud_state="FULL"):
    precip_tau = math.log(2.0) - 0.1 - 0.1 - 0.2 - 0.1
    row = {
        "time": "2026-09-09T10:00:00+00:00",
        "solar_altitude_deg": -4.0,
        "reference_receiver_id": "redref::phase1",
        "direction_offset_deg": 0.0,
        "distance_km": 10.0,
        "sampled_receiver_altitude_km": 4.0,
        "voxel_bottom_km": 3.75,
        "voxel_top_km": 4.25,
        "v1_direct_solar_fraction": 1.0,
        "red_light_path_state": "RED_LIGHT_PATH_OPEN" if cloud_state == "FULL" else "RED_LIGHT_PATH_CONFLICT",
        "red_light_path_evidence_complete": cloud_state == "FULL",
        "red_light_cloud_evidence_state": cloud_state,
        "red_light_aerosol_evidence_state": "FULL_EXACT_VALID_TIME",
        "red_light_gas_evidence_state": "FULL",
        "red_light_precipitation_evidence_state": "FULL",
        "resolved_upstream_cloud_tau": 0.1 if cloud_state == "FULL" else None,
    }
    for wavelength in SIX_BAND_WAVELENGTHS_NM:
        w = int(wavelength)
        row[f"rayleigh_tau_{w}nm"] = 0.1
        row[f"aerosol_tau_{w}nm"] = 0.1
        row[f"gas_tau_{w}nm"] = 0.2
        row[f"gas_tau_o3_{w}nm"] = 0.05
        row[f"tau_precip_{w}nm"] = precip_tau
        row[f"red_light_availability_{w}nm"] = 0.5 if cloud_state == "FULL" else None
    return pd.DataFrame([row])


def _gas_profiles():
    rows = []
    for distance in (0.0, 10.0):
        for altitude, pressure, temperature in (
            (0.0, 1013.25, 288.15),
            (6.0, 472.0, 249.0),
            (15.0, 120.0, 216.0),
        ):
            rows.append({
                "time": "2026-09-09T10:00:00+00:00",
                "solar_altitude_deg": -4.0,
                "direction_offset_deg": 0.0,
                "distance_km": distance,
                "altitude_agl_km": altitude,
                "temperature_k": temperature,
                "pressure_hpa": pressure,
                "o2_mole_fraction": 0.20946,
                "h2o_mole_fraction": 0.005,
                "o3_mole_fraction": 5e-8,
            })
    return pd.DataFrame(rows)


def _observer_rt(targets, *_args, **_kwargs):
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


def _build(monkeypatch, *, cloud_state="FULL"):
    monkeypatch.setattr(twilight_glow, "_observer_precipitation", lambda *_a, **_k: pd.DataFrame())
    monkeypatch.setattr(twilight_glow, "build_viewing_spectral_extinction", _observer_rt)
    monkeypatch.setattr(
        twilight_glow,
        "_observer_gas_species_path",
        lambda *_a, **_k: (
            {int(w): {"o3": 0.02, "non_o3": 0.08, "total": 0.1} for w in SIX_BAND_WAVELENGTHS_NM},
            "GLOW_OBSERVER_GAS_PATH_RESOLVED",
            1, 1, 10.0,
        ),
    )
    detail, summary = twilight_glow.build_twilight_glow_branch(
        red_light_reference=_red_reference(cloud_state=cloud_state),
        event_timeline=_timeline(),
        cloud_layers=pd.DataFrame(),
        target_optics=pd.DataFrame(),
        aerosol_snapshots=pd.DataFrame(),
        gas_profiles=_gas_profiles(),
        route_snapshots=pd.DataFrame(),
        observer_lat_deg=25.04,
        observer_lon_deg=121.52,
    )
    sun, observer, single = twilight_glow.build_twilight_glow_phase1_exports(detail)
    return detail, summary, sun, observer, single


def test_phase1_explicit_six_band_extinction_closes_without_o3_double_count(monkeypatch):
    detail, _, sun, observer, single = _build(monkeypatch)
    assert len(detail) == len(sun) == len(observer) == len(single) == 1
    sr = sun.iloc[0]
    vr = observer.iloc[0]
    cr = single.iloc[0]
    for wavelength in SIX_BAND_WAVELENGTHS_NM:
        w = int(wavelength)
        assert math.isclose(sr[f"glow_sun_tau_gas_non_o3_{w}nm"], 0.15, abs_tol=1e-12)
        assert math.isclose(sr[f"glow_sun_tau_o3_{w}nm"], 0.05, abs_tol=1e-12)
        assert math.isclose(sr[f"glow_sun_tau_total_{w}nm"], math.log(2.0), abs_tol=1e-12)
        assert math.isclose(sr[f"glow_sun_transmission_{w}nm"], 0.5, abs_tol=1e-12)
        assert math.isclose(sr[f"glow_sun_incident_relative_irradiance_{w}nm"], 0.5, abs_tol=1e-12)
        assert sr[f"glow_sun_band_evidence_state_{w}nm"] == "FULL"

        ray = vr[f"glow_observer_tau_rayleigh_{w}nm"]
        expected_observer = ray + 0.08 + 0.02 + 0.02
        assert math.isclose(vr[f"glow_observer_tau_total_{w}nm"], expected_observer, abs_tol=1e-12)
        assert math.isclose(vr[f"glow_observer_transmission_{w}nm"], math.exp(-expected_observer), abs_tol=1e-12)
        assert vr[f"glow_observer_band_evidence_state_{w}nm"] == "FULL"

        expected_proxy = (
            sr[f"glow_sun_incident_relative_irradiance_{w}nm"]
            * vr[f"glow_observer_transmission_{w}nm"]
            * cr[f"glow_rayleigh_source_coefficient_m1_sr_{w}nm"]
        )
        assert math.isclose(cr[f"glow_single_scattering_source_proxy_{w}nm"], expected_proxy, rel_tol=1e-12)
    assert cr["glow_result_role"] == "INDEPENDENT_DIAGNOSTIC_ONLY"
    assert not cr["calibrated_glow_radiance_available"]


def test_phase1_missing_cloud_evidence_does_not_promote_sun_total_or_proxy(monkeypatch):
    detail, _, sun, _, single = _build(monkeypatch, cloud_state="DIRECT_EVIDENCE_CONFLICT")
    assert detail.iloc[0]["glow_proxy_state"] == "GLOW_RAYLEIGH_SINGLE_SCATTERING_UNRESOLVED"
    for wavelength in SIX_BAND_WAVELENGTHS_NM:
        w = int(wavelength)
        assert sun.iloc[0][f"glow_sun_band_evidence_state_{w}nm"] == "MISSING"
        assert pd.isna(sun.iloc[0][f"glow_sun_tau_total_{w}nm"])
        assert pd.isna(sun.iloc[0][f"glow_sun_transmission_{w}nm"])
        assert pd.isna(sun.iloc[0][f"glow_sun_incident_relative_irradiance_{w}nm"])
        assert pd.isna(single.iloc[0][f"glow_single_scattering_source_proxy_{w}nm"])


def test_phase1_integrity_guards_cover_exports_and_arithmetic(monkeypatch):
    detail, summary, sun, observer, single = _build(monkeypatch)
    formation = _timeline()[["time", "solar_altitude_deg"]].copy()
    formation["formation_state"] = "UNCERTAIN_OPTICS"
    payload = {
        "v1_formation": formation,
        "v1_twilight_glow_scattering_volume_550_750nm": detail,
        "v1_twilight_glow_sun_to_scatter_extinction_550_750nm": sun,
        "v1_twilight_glow_scatter_to_observer_extinction_550_750nm": observer,
        "v1_twilight_glow_single_scattering_550_750nm": single,
        "v1_twilight_glow_summary": summary,
        "twilight_glow_required": True,
        "twilight_glow_extinction_phase1_required": True,
    }
    statuses = build_analysis_integrity_audit(payload).set_index("check_id")["status"].to_dict()
    for check_id in (
        "TWILIGHT_GLOW_SUN_TO_SCATTER_TARGET_COVERAGE",
        "TWILIGHT_GLOW_SCATTER_TO_OBSERVER_TARGET_COVERAGE",
        "TWILIGHT_GLOW_SIX_BAND_EXTINCTION_SCHEMA",
        "TWILIGHT_GLOW_SUN_PATH_NUMERIC_CLOSURE",
        "TWILIGHT_GLOW_OBSERVER_PATH_NUMERIC_CLOSURE",
        "TWILIGHT_GLOW_SINGLE_SCATTERING_NUMERIC_CLOSURE",
        "TWILIGHT_GLOW_NO_FALSE_RADIANCE_CLAIM",
    ):
        assert statuses[check_id] == "PASS"

    broken_sun = sun.copy()
    broken_sun.loc[0, "glow_sun_tau_total_650nm"] += 0.2
    broken = build_analysis_integrity_audit({**payload, "v1_twilight_glow_sun_to_scatter_extinction_550_750nm": broken_sun})
    broken_status = broken.set_index("check_id")["status"].to_dict()
    assert broken_status["TWILIGHT_GLOW_SUN_PATH_NUMERIC_CLOSURE"] == "FAIL"

    sparse_observer = observer.iloc[0:0].copy()
    sparse = build_analysis_integrity_audit({**payload, "v1_twilight_glow_scatter_to_observer_extinction_550_750nm": sparse_observer})
    sparse_status = sparse.set_index("check_id")["status"].to_dict()
    assert sparse_status["TWILIGHT_GLOW_SCATTER_TO_OBSERVER_TARGET_COVERAGE"] == "FAIL"


def test_phase1_production_handoff_and_case_members_are_explicit():
    root = Path(__file__).resolve().parents[1]
    model = (root / "firecloud" / "model.py").read_text(encoding="utf-8")
    app = (root / "app.py").read_text(encoding="utf-8")
    for key in (
        "v1_twilight_glow_sun_to_scatter_extinction_550_750nm",
        "v1_twilight_glow_scatter_to_observer_extinction_550_750nm",
        "v1_twilight_glow_single_scattering_550_750nm",
    ):
        assert key in model
        assert f'"{key}.csv"' in app

    manifest = pd.DataFrame({"artifact": [
        "summary.csv", "route_reference_contract.csv", "route_points.csv", "forecast_raw.csv",
        "performance_diagnostics.csv", "gfs_native_request_audit.csv", "gfs_grib_message_inventory.csv",
        "gfs_native_field_completeness.csv", "v1_formation.csv", "v1_viewing_summary.csv",
        "v1_viewing_precipitation_evidence.csv", "v1_viewing_spectral_extinction_550_750nm.csv",
        "v1_viewing_spectral_summary.csv", "v1_twilight_glow_scattering_volume_550_750nm.csv",
        "v1_twilight_glow_sun_to_scatter_extinction_550_750nm.csv",
        "v1_twilight_glow_scatter_to_observer_extinction_550_750nm.csv",
        "v1_twilight_glow_single_scattering_550_750nm.csv",
        "v1_twilight_glow_aerosol_scattering_550_750nm.csv", "v1_twilight_glow_summary.csv",
        "v1_photography_decision.csv", "analysis_integrity_audit.csv",
    ]})
    audit = build_archive_integrity_audit(manifest, pd.DataFrame([{"status": "PASS"}]))
    assert audit.iloc[-1]["status"] == "PASS"
