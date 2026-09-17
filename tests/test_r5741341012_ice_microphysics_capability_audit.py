import json
from pathlib import Path

import numpy as np
import pandas as pd

import firecloud
from firecloud.ice_cloud_spectral_optics import (
    ICE_OPTICS_WAVELENGTHS_NM,
    IceOpticsLUTStatus,
    build_ice_cloud_spectral_optics_runtime,
    validate_ice_optics_lut,
)
from firecloud.ice_microphysics_capability import (
    SCIENCE_BASELINE,
    ICE_PHASE2_MODE,
    build_native_microphysics_capability_audit,
    build_mapping_eligibility_summary,
    phase2_contract_payload,
)


def _fake_lut():
    rows = []
    for dmax, reff in [(40.0, 20.0), (80.0, 40.0)]:
        for wl in ICE_OPTICS_WAVELENGTHS_NM:
            rows.append({
                "wavelength_nm": wl,
                "maximum_dimension_um": dmax,
                "effective_diameter_um": 2.0 * reff,
                "effective_radius_um": reff,
                "ice_habit": "8_columns",
                "surface_roughness": "Rough050",
                "mass_extinction_coefficient_m2_kg": 120.0 + wl / 1000.0,
                "single_scattering_albedo": 0.999,
                "asymmetry_parameter": 0.75,
                "source_dataset": "TEST_ONLY",
                "source_version": "v1",
                "source_record_provenance": "TEST_ONLY",
            })
    return validate_ice_optics_lut(pd.DataFrame(rows))


def _gfs_inventory():
    rows = []
    for sn, canonical, units in [
        ("ICMR", "cloud_ice_water_kgkg", "kg kg-1"),
        ("CLWMR", "cloud_liquid_water_kgkg", "kg kg-1"),
        ("TMP", "temperature_k", "K"),
        ("RH", "relative_humidity_pct", "%"),
        ("TCDC", "cloud_fraction", "%"),
        ("HGT", "geopotential_height_m", "gpm"),
    ]:
        rows.append({
            "shortName": sn,
            "recognized_as": canonical,
            "typeOfLevel": "isobaricInhPa",
            "level": 500.0,
            "units": units,
            "message_count": 1,
            "gfs_run_utc": "2026-09-16T00:00:00+00:00",
            "gfs_forecast_hour": 6,
            "gfs_valid_time_utc": "2026-09-16T06:00:00+00:00",
        })
    return pd.DataFrame(rows)


def _gfs_completeness():
    rows = []
    for sn in ["ICMR", "CLWMR", "TMP", "RH", "TCDC", "HGT", "RWMR", "SNMR", "GRLE"]:
        rows.append({
            "field": sn,
            "status": "READY" if sn in {"ICMR", "CLWMR", "TMP", "RH", "TCDC", "HGT"} else "MISSING",
            "message_count": 1 if sn in {"ICMR", "CLWMR", "TMP", "RH", "TCDC", "HGT"} else 0,
            "icmr_nonnull_route_values": 20 if sn == "ICMR" else np.nan,
            "clwmr_nonnull_route_values": 20 if sn == "CLWMR" else np.nan,
            "gfs_run_utc": "2026-09-16T00:00:00+00:00",
            "gfs_forecast_hour": 6,
            "gfs_valid_time_utc": "2026-09-16T06:00:00+00:00",
        })
    return pd.DataFrame(rows)


def test_version_and_frozen_phase2_mode():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.25"
    assert SCIENCE_BASELINE == "R5.7.41.2_SHADOW_COT_AB_FROZEN"
    assert ICE_PHASE2_MODE == "DIAGNOSTIC_READINESS_ONLY"


def test_icmr_iwp_temperature_rh_cloud_fraction_do_not_auto_create_dmax():
    lut = _fake_lut()
    status = IceOpticsLUTStatus(True, "test.csv", len(lut), True, "ICE_OPTICS_LUT_READY")
    native = pd.DataFrame([{
        "solar_altitude_deg": -2.0,
        "direction_offset_deg": 0.0,
        "distance_km": 60.0,
        "native_vertical_completeness": 1.0,
        "ice_water_path_proxy_gm3_km": 0.02,
        "cloud_ice_water_kgkg": 2.0e-5,
        "temperature_k": 248.0,
        "relative_humidity_pct": 92.0,
        "cloud_fraction": 0.85,
        # Deliberately no Dmax/habit/roughness.
    }])
    runtime = build_ice_cloud_spectral_optics_runtime(native, lut=lut, lut_status=status)
    row = runtime.iloc[0]
    assert row["ice_optics_state"] == "ICE_MAXIMUM_DIMENSION_MISSING"
    assert row["ice_optics_missing_reason"] == "NO_NATIVE_OR_CALIBRATED_ICE_DMAX"
    assert pd.isna(row["ice_maximum_dimension_um"])
    assert str(row["ice_habit"]).upper() == "UNKNOWN"
    assert str(row["surface_roughness"]).upper() == "UNKNOWN"
    assert row["tau_synthesis_allowed"] is False or not bool(row["tau_synthesis_allowed"])
    assert row["formation_promotion_allowed"] is False or not bool(row["formation_promotion_allowed"])
    assert all(pd.isna(row[f"tau_ice_{wl}"]) for wl in ICE_OPTICS_WAVELENGTHS_NM)


def test_reff_is_not_dmax_even_with_all_context_fields_present():
    lut = _fake_lut()
    status = IceOpticsLUTStatus(True, "test.csv", len(lut), True, "ICE_OPTICS_LUT_READY")
    native = pd.DataFrame([{
        "solar_altitude_deg": -2.0,
        "direction_offset_deg": 0.0,
        "distance_km": 60.0,
        "native_vertical_completeness": 1.0,
        "ice_water_path_proxy_gm3_km": 0.02,
        "ice_effective_radius_um": 30.0,
        "temperature_k": 248.0,
        "relative_humidity_pct": 92.0,
        "cloud_fraction": 0.85,
        "native_cloud_thickness_km": 3.0,
        "ice_habit": "8_columns",
        "ice_surface_roughness": "Rough050",
    }])
    runtime = build_ice_cloud_spectral_optics_runtime(native, lut=lut, lut_status=status)
    row = runtime.iloc[0]
    assert row["ice_effective_radius_um"] == 30.0
    assert pd.isna(row["ice_maximum_dimension_um"])
    assert row["ice_optics_state"] == "ICE_MAXIMUM_DIMENSION_MISSING"


def test_capability_audit_labels_native_derived_runtime_and_missing_psd_separately():
    vox = pd.DataFrame([{ "ice_water_content_gm3": 0.02, "native_microphysics_supported": True }])
    cols = pd.DataFrame([{
        "ice_water_path_proxy_gm3_km": 0.02,
        "native_vertical_completeness": 1.0,
    }])
    runtime = pd.DataFrame([{
        "native_iwp_kg_m2": 0.02,
        "ice_maximum_dimension_um": np.nan,
        "ice_effective_radius_um": np.nan,
        "ice_habit": "UNKNOWN",
        "surface_roughness": "UNKNOWN",
        "formation_promotion_allowed": False,
    }])
    audit = build_native_microphysics_capability_audit(
        _gfs_inventory(), _gfs_completeness(), vox, cols, runtime
    )
    by = audit.set_index("field_short_name")
    assert bool(by.loc["ICMR", "native_message_present"])
    assert by.loc["ICMR", "native_vs_derived"] == "NATIVE_GFS"
    assert "MASS_INPUT_ONLY" in by.loc["ICMR", "dmax_mapping_role"]
    assert by.loc["DERIVED_IWP", "native_vs_derived"] == "DETERMINISTIC_DERIVED"
    assert "not a GFS native field" in by.loc["DERIVED_IWP", "source_provenance"]
    assert by.loc["RUNTIME_DMAX", "native_vs_derived"] == "RUNTIME_SLOT"
    assert int(by.loc["RUNTIME_DMAX", "nonnull_count"]) == 0
    assert by.loc["PSD_SIZE_BINS", "eligibility_state"] == "INSUFFICIENT_PSD_INPUTS"
    assert by.loc["PSD_NUMBER_CONCENTRATION", "eligibility_state"] == "INSUFFICIENT_PSD_INPUTS"
    assert not audit["physics_promotion_allowed"].astype(bool).any()


def test_mapping_summary_fails_closed_for_positive_iwp_without_legal_size_psd_habit_roughness():
    vox = pd.DataFrame([{ "ice_water_content_gm3": 0.02, "native_microphysics_supported": True }])
    cols = pd.DataFrame([{
        "ice_water_path_proxy_gm3_km": 0.02,
        "native_vertical_completeness": 1.0,
    }])
    runtime = pd.DataFrame([{
        "native_iwp_kg_m2": 0.02,
        "ice_maximum_dimension_um": np.nan,
        "ice_effective_radius_um": np.nan,
        "ice_habit": "UNKNOWN",
        "surface_roughness": "UNKNOWN",
    }])
    audit = build_native_microphysics_capability_audit(
        _gfs_inventory(), _gfs_completeness(), vox, cols, runtime
    )
    summary = build_mapping_eligibility_summary(audit, cols, runtime).iloc[0]
    assert bool(summary["NATIVE_ICE_MASS_INPUT_READY"])
    assert bool(summary["NATIVE_THERMODYNAMIC_CONTEXT_READY"])
    assert bool(summary["NATIVE_VERTICAL_PROFILE_SUPPORT"])
    assert not bool(summary["NATIVE_DMAX_AVAILABLE"])
    assert not bool(summary["CALIBRATED_DMAX_MAPPING_AVAILABLE"])
    assert not bool(summary["NATIVE_PSD_AVAILABLE"])
    assert not bool(summary["CALIBRATED_PSD_MAPPING_AVAILABLE"])
    assert not bool(summary["MICROPHYSICS_MAPPING_READY"])
    assert not bool(summary["SINGLE_PARTICLE_LUT_LOOKUP_ELIGIBLE"])
    assert not bool(summary["BULK_PSD_SYNTHESIS_ELIGIBLE"])
    assert not bool(summary["PRODUCTION_ICE_OPTICS_READY"])
    assert not bool(summary["physics_promotion_allowed"])
    assert summary["eligibility_state"] == "INSUFFICIENT_MICROPHYSICS"
    for blocker in [
        "ICE_DMAX_NATIVE_FIELD_UNAVAILABLE",
        "ICE_DMAX_MAPPING_UNAVAILABLE",
        "ICE_PSD_INPUT_INCOMPLETE",
        "ICE_HABIT_UNRESOLVED",
        "ICE_ROUGHNESS_UNRESOLVED",
    ]:
        assert blocker in summary["eligibility_blockers"]


def test_contract_forbids_assumption_based_mapping_and_case_members_are_wired():
    contract = phase2_contract_payload(physicscore_version=firecloud.__version__)
    forbidden = set(contract["forbidden_implicit_mappings"])
    assert "effective_radius_um_to_maximum_dimension_um" in forbidden
    assert "IWP_to_Dmax" in forbidden
    assert "temperature_or_cloud_regime_to_habit" in forbidden
    assert "fixed_surface_roughness_default" in forbidden
    assert contract["physics_promotion_allowed"] is False
    assert contract["frozen_science_unchanged"] is True

    app_text = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")
    assert '"ice_microphysics_native_input_capability_audit.csv"' in app_text
    assert '"ice_microphysics_phase2_mapping_eligibility.csv"' in app_text
    assert '"ice_microphysics_phase2_contract.json"' in app_text
