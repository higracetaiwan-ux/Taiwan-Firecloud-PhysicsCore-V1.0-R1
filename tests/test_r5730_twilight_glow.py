from pathlib import Path
import math

import pandas as pd

from firecloud.case_integrity import build_analysis_integrity_audit
from firecloud.contracts import (
    CORE_FIRECLOUD_ANGLES_DEG,
    SIX_BAND_WAVELENGTHS_NM,
    TwilightGlowResult,
)
import firecloud.twilight_glow as twilight_glow


def _timeline(angles=(-4.0,)):
    return pd.DataFrame([
        {
            "time": f"2026-09-09T10:{index:02d}:00+00:00",
            "solar_altitude_deg": angle,
            "solar_azimuth_deg": 270.0,
        }
        for index, angle in enumerate(angles)
    ])


def _red_reference(timeline):
    rows = []
    for index, event in timeline.iterrows():
        row = {
            "time": event["time"],
            "solar_altitude_deg": event["solar_altitude_deg"],
            "reference_receiver_id": f"redref::{index}",
            "direction_offset_deg": 0.0,
            "distance_km": 10.0,
            "sampled_receiver_altitude_km": 4.0,
            "voxel_bottom_km": 3.75,
            "voxel_top_km": 4.25,
            "v1_direct_solar_fraction": 1.0,
            "red_light_path_state": "RED_LIGHT_PATH_FULL",
            "red_light_path_evidence_complete": True,
        }
        for wavelength in SIX_BAND_WAVELENGTHS_NM:
            row[f"red_light_availability_{int(wavelength)}nm"] = 0.5
        rows.append(row)
    return pd.DataFrame(rows)


def _gas_profiles(timeline):
    rows = []
    for _, event in timeline.iterrows():
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
        }
        for wavelength in SIX_BAND_WAVELENGTHS_NM:
            row[f"view_tau_total_{int(wavelength)}nm"] = 0.1
        rows.append(row)
    return pd.DataFrame(rows)


def _complete_branch(monkeypatch, angles=(-4.0,)):
    timeline = _timeline(angles)
    monkeypatch.setattr(twilight_glow, "_observer_precipitation", lambda *_a, **_k: pd.DataFrame())
    monkeypatch.setattr(twilight_glow, "build_viewing_spectral_extinction", _full_observer_rt)
    detail, summary = twilight_glow.build_twilight_glow_branch(
        red_light_reference=_red_reference(timeline),
        event_timeline=timeline,
        cloud_layers=pd.DataFrame(),
        target_optics=pd.DataFrame(),
        aerosol_snapshots=pd.DataFrame(),
        gas_profiles=_gas_profiles(timeline),
        route_snapshots=pd.DataFrame(),
        observer_lat_deg=25.04,
        observer_lon_deg=121.52,
    )
    return timeline, detail, summary


def test_rayleigh_cross_section_decreases_across_six_bands():
    values = [twilight_glow.rayleigh_cross_section_m2(w) for w in SIX_BAND_WAVELENGTHS_NM]
    assert all(value > 0.0 for value in values)
    assert values == sorted(values, reverse=True)
    assert math.isclose(
        twilight_glow.rayleigh_phase_function_sr(90.0),
        3.0 / (16.0 * math.pi),
        rel_tol=0.0,
        abs_tol=1e-15,
    )


def test_complete_branch_resolves_six_band_rayleigh_source_proxy(monkeypatch):
    _, detail, summary = _complete_branch(monkeypatch)
    assert len(detail) == 1
    row = detail.iloc[0]
    assert row["glow_proxy_state"] == "GLOW_RAYLEIGH_SINGLE_SCATTERING_PROXY_READY"
    assert row["formation_independent"]
    assert row["viewing_independent"]
    assert not row["calibrated_glow_radiance_available"]
    assert "score" not in " ".join(detail.columns).lower()
    assert "decision" not in " ".join(detail.columns).lower()
    for wavelength in SIX_BAND_WAVELENGTHS_NM:
        tau = row[f"glow_observer_total_tau_{int(wavelength)}nm"]
        transmission = row[f"glow_observer_total_transmission_{int(wavelength)}nm"]
        coefficient = row[f"glow_rayleigh_source_coefficient_m1_sr_{int(wavelength)}nm"]
        proxy = row[f"glow_single_scattering_source_proxy_{int(wavelength)}nm"]
        assert tau > 0.1
        assert math.isclose(transmission, math.exp(-tau), abs_tol=1e-12)
        assert math.isclose(proxy, 0.5 * transmission * coefficient, rel_tol=1e-12)
        assert row[f"glow_band_evidence_state_{int(wavelength)}nm"] == "FULL_RAYLEIGH_PROXY"
    assert summary.iloc[0]["twilight_glow_state"] == "GLOW_RAYLEIGH_PROXY_READY"


def test_missing_observer_rt_stays_partial_without_final_proxy(monkeypatch):
    timeline = _timeline()
    monkeypatch.setattr(twilight_glow, "_observer_precipitation", lambda *_a, **_k: pd.DataFrame())
    monkeypatch.setattr(twilight_glow, "build_viewing_spectral_extinction", lambda *_a, **_k: pd.DataFrame())
    detail, _ = twilight_glow.build_twilight_glow_branch(
        red_light_reference=_red_reference(timeline),
        event_timeline=timeline,
        cloud_layers=pd.DataFrame(), target_optics=pd.DataFrame(),
        aerosol_snapshots=pd.DataFrame(), gas_profiles=_gas_profiles(timeline),
        route_snapshots=pd.DataFrame(), observer_lat_deg=25.04, observer_lon_deg=121.52,
    )
    row = detail.iloc[0]
    assert row["glow_proxy_state"] == "GLOW_RAYLEIGH_SINGLE_SCATTERING_PROXY_PARTIAL"
    assert "SCATTER_TO_OBSERVER_EXTINCTION" in row["glow_missing_components"]
    for wavelength in SIX_BAND_WAVELENGTHS_NM:
        assert pd.isna(row[f"glow_observer_total_tau_{int(wavelength)}nm"])
        assert pd.isna(row[f"glow_single_scattering_source_proxy_{int(wavelength)}nm"])


def test_summary_retains_all_thirteen_runtime_angles_when_evidence_is_empty():
    timeline = _timeline(CORE_FIRECLOUD_ANGLES_DEG)
    summary = twilight_glow.summarize_twilight_glow(pd.DataFrame(), timeline)
    assert len(summary) == 13
    assert set(summary["solar_altitude_deg"]) == set(CORE_FIRECLOUD_ANGLES_DEG)
    assert summary["twilight_glow_state"].eq("GLOW_EVIDENCE_UNAVAILABLE").all()


def test_integrity_accepts_complete_branch_and_rejects_tampering(monkeypatch):
    timeline, detail, summary = _complete_branch(monkeypatch)
    formation = timeline[["time", "solar_altitude_deg"]].copy()
    formation["formation_state"] = "UNCERTAIN_OPTICS"
    base = {
        "v1_formation": formation,
        "v1_twilight_glow_scattering_volume_550_750nm": detail,
        "v1_twilight_glow_summary": summary,
        "twilight_glow_required": True,
    }
    statuses = build_analysis_integrity_audit(base).set_index("check_id")["status"].to_dict()
    for check_id in (
        "TWILIGHT_GLOW_ANGLE_COVERAGE",
        "TWILIGHT_GLOW_VOLUME_KEY_UNIQUENESS",
        "TWILIGHT_GLOW_SIX_BAND_SCHEMA",
        "TWILIGHT_GLOW_NUMERIC_CLOSURE",
        "TWILIGHT_GLOW_BRANCH_INDEPENDENCE",
        "TWILIGHT_GLOW_NO_FALSE_RADIANCE_CLAIM",
    ):
        assert statuses[check_id] == "PASS"

    tampered = detail.copy()
    tampered.loc[0, "glow_single_scattering_source_proxy_650nm"] *= 2.0
    broken = build_analysis_integrity_audit({**base, "v1_twilight_glow_scattering_volume_550_750nm": tampered})
    broken_statuses = broken.set_index("check_id")["status"].to_dict()
    assert broken_statuses["TWILIGHT_GLOW_NUMERIC_CLOSURE"] == "FAIL"


def test_contract_and_production_pipeline_handoff_are_explicit():
    contract = TwilightGlowResult(
        solar_angle_deg=-4.0,
        spectral_single_scattering_source_proxy={650: None},
        glow_state="MISSING",
        evidence_completeness=0.0,
        aerosol_scattering_state="NOT_RESOLVED",
        multiple_scattering_state="NOT_RESOLVED",
    )
    assert not contract.calibrated_radiance_available

    root = Path(__file__).resolve().parents[1]
    model = (root / "firecloud" / "model.py").read_text(encoding="utf-8")
    app = (root / "app.py").read_text(encoding="utf-8")
    start = model.index("_pre_integrity_result = {")
    end = model.index("analysis_integrity_audit = build_analysis_integrity_audit", start)
    handoff = model[start:end]
    assert handoff.count('"v1_twilight_glow_scattering_volume_550_750nm"') == 1
    assert '"twilight_glow_required": True' in handoff
    assert '"v1_twilight_glow_scattering_volume_550_750nm.csv"' in app
    assert '"v1_twilight_glow_summary.csv"' in app
