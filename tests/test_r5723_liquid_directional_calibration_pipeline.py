from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd
import pytest

from firecloud.contracts import SIX_BAND_WAVELENGTHS_NM
from firecloud.tier2_directional_scattering_calibration import (
    DIRECTIONAL_GEOMETRY_CONVENTION,
    DIRECTIONAL_RESPONSE_DEFINITION,
    DIRECTIONAL_RESPONSE_UNITS,
    DIRECTIONAL_CALIBRATION_CONTRACT,
)
from firecloud.tier2_libradtran_mystic_adapter import (
    MYSTIC_ADAPTER_CONTRACT, INCIDENT_IRRADIANCE_REFERENCE, ATMOSPHERIC_COUPLING,
    SURFACE_BOUNDARY, CALIBRATION_SCOPE,
)
from firecloud.tier2_directional_scattering_runtime import validate_directional_lut_bytes
from firecloud.tier2_liquid_directional_calibration_pipeline import (
    DOMAIN_CONTRACT,
    EXTERNAL_RESULT_REQUIRED_COLUMNS,
    PIPELINE_CONTRACT,
    RESULT_CONTRACT,
    SOLVER_RECIPE_CONTRACT,
    build_external_job_table,
    build_libradtran_mystic_solver_recipe,
    build_production_lut_from_external_results,
    plan_liquid_directional_calibration_domain,
    select_liquid_calibration_targets,
    uvspec_template_text,
    validate_external_rt_results,
    write_external_calibration_bundle,
)


def _fixture_tables():
    foundation = pd.DataFrame(
        [
            {"time": "2026-09-08T09:32:00Z", "solar_altitude_deg": 0.0, "canvas_id": "A", "cloud_layer_id": "L1", "operational_domain": "PRIMARY_CANVAS", "distance_km": 40.0, "solar_zenith_deg": 89.1, "view_zenith_deg": 90.1, "relative_azimuth_deg": 175.0, "scattering_angle_deg": 2.0, "directional_geometry_state": "FULL_DIRECTIONAL_GEOMETRY_READY"},
            {"time": "2026-09-08T09:42:00Z", "solar_altitude_deg": -2.0, "canvas_id": "B", "cloud_layer_id": "L2", "operational_domain": "PRIMARY_CANVAS", "distance_km": 60.0, "solar_zenith_deg": 93.9, "view_zenith_deg": 91.4, "relative_azimuth_deg": 179.9, "scattering_angle_deg": 6.8, "directional_geometry_state": "FULL_DIRECTIONAL_GEOMETRY_READY"},
            {"time": "2026-09-08T09:52:00Z", "solar_altitude_deg": -4.0, "canvas_id": "C", "cloud_layer_id": "L3", "operational_domain": "EXTENDED_CANVAS", "distance_km": 90.0, "solar_zenith_deg": 95.5, "view_zenith_deg": 91.8, "relative_azimuth_deg": 178.0, "scattering_angle_deg": 8.0, "directional_geometry_state": "FULL_DIRECTIONAL_GEOMETRY_READY"},
            {"time": "2026-09-08T09:52:00Z", "solar_altitude_deg": -4.0, "canvas_id": "D", "cloud_layer_id": "L4", "operational_domain": "EXTENDED_CANVAS", "distance_km": 95.0, "solar_zenith_deg": 95.0, "view_zenith_deg": 91.7, "relative_azimuth_deg": 178.0, "scattering_angle_deg": 8.0, "directional_geometry_state": "FULL_DIRECTIONAL_GEOMETRY_READY"},
            {"time": "2026-09-08T09:52:00Z", "solar_altitude_deg": -4.0, "canvas_id": "E", "cloud_layer_id": "L5", "operational_domain": "EXTENDED_CANVAS", "distance_km": 98.0, "solar_zenith_deg": 95.0, "view_zenith_deg": 91.7, "relative_azimuth_deg": 178.0, "scattering_angle_deg": 8.0, "directional_geometry_state": "FULL_DIRECTIONAL_GEOMETRY_READY"},
        ]
    )
    readiness = pd.DataFrame(
        [
            {"solar_altitude_deg": 0.0, "canvas_id": "A", "target_optical_truth_state": "EXACT_PRIMARY_NATIVE", "target_cot_semantics": "EXACT_VALUE", "cot_lower_bound": 0.5, "cot_upper_bound": 0.5, "phase": "LIQUID", "effective_radius_um": 10.0, "cloud_thickness_km": 1.2, "tier2_input_contract_state": "INPUTS_READY_AWAITING_LUT_SOLVER"},
            {"solar_altitude_deg": -2.0, "canvas_id": "B", "target_optical_truth_state": "BOUNDED_NATIVE_BRACKET", "target_cot_semantics": "BOUNDED_INTERVAL", "cot_lower_bound": 1.0, "cot_upper_bound": 3.0, "phase": "WATER", "effective_radius_um": 12.0, "cloud_thickness_km": 1.5, "tier2_input_contract_state": "INPUTS_READY_AWAITING_LUT_SOLVER"},
            {"solar_altitude_deg": -4.0, "canvas_id": "C", "target_optical_truth_state": "EXACT_SECONDARY_NATIVE", "target_cot_semantics": "EXACT_VALUE", "cot_lower_bound": 7.5, "cot_upper_bound": 7.5, "phase": "ICE", "effective_radius_um": 20.0, "cloud_thickness_km": 2.0, "tier2_input_contract_state": "INPUTS_READY_AWAITING_LUT_SOLVER"},
            {"solar_altitude_deg": -4.0, "canvas_id": "D", "target_optical_truth_state": "OPTICS_UNKNOWN", "target_cot_semantics": "UNRESOLVED_MISSING", "cot_lower_bound": None, "cot_upper_bound": None, "phase": "LIQUID", "effective_radius_um": 10.0, "cloud_thickness_km": 2.0, "tier2_input_contract_state": "INPUTS_READY_AWAITING_LUT_SOLVER"},
            {"solar_altitude_deg": -4.0, "canvas_id": "E", "target_optical_truth_state": "EXACT_PRIMARY_NATIVE", "target_cot_semantics": "EXACT_VALUE", "cot_lower_bound": 2.0, "cot_upper_bound": 2.0, "phase": "LIQUID", "effective_radius_um": 10.0, "cloud_thickness_km": 2.0, "tier2_input_contract_state": "INPUTS_BLOCKED_TARGET_OPTICS"},
        ]
    )
    return foundation, readiness


def _tiny_domain():
    return {
        "contract": DOMAIN_CONTRACT,
        "pipeline_contract": PIPELINE_CONTRACT,
        "phases": ["LIQUID"],
        "wavelengths_nm": list(SIX_BAND_WAVELENGTHS_NM),
        "cot": [0.5, 2.0],
        "effective_radius_um": [10.0],
        "solar_zenith_deg": [90.0, 94.0],
        "view_zenith_deg": [90.0, 92.0],
        "relative_azimuth_deg": [175.0, 180.0],
    }


def _results_for_jobs(jobs: pd.DataFrame, sigma=0.005):
    rows = []
    for row in jobs.itertuples(index=False):
        # Test fixture only. This deterministic formula is never installed as a production LUT.
        response = 0.01 + 0.001 * float(row.cot) + 0.00001 * float(row.wavelength_nm)
        std = response * float(sigma)
        rows.append({
            "job_id": row.job_id,
            "response_factor": response,
            "response_factor_std": std,
            "mc_absolute_sigma": std,
            "mc_relative_sigma": sigma,
            "photon_count": int(row.mc_photons),
            "sample_qc_state": "PASS",
            "solver_run_id": f"TEST-RUN:{row.job_id}",
            "solver_exit_code": 0,
            "solver_family": "LIBRADTRAN_UVSPEC_MYSTIC",
            "solver_version": "test-external-rt-1",
            "result_contract": RESULT_CONTRACT,
            "adapter_contract": MYSTIC_ADAPTER_CONTRACT,
        })
    return pd.DataFrame(rows, columns=EXTERNAL_RESULT_REQUIRED_COLUMNS)


def test_selector_retains_only_real_ready_liquid_exact_or_bounded_targets():
    f, r = _fixture_tables()
    q = select_liquid_calibration_targets(foundation=f, readiness=r)
    assert list(q["canvas_id"]) == ["A", "B"]
    assert set(q["phase"]) == {"LIQUID"}
    assert set(q["calibration_target_state"]) == {"REAL_TIER2_READY_LIQUID_TARGET"}
    assert set(q["calibration_pipeline_contract"]) == {PIPELINE_CONTRACT}


def test_domain_planner_brackets_real_targets_and_keeps_thickness_out_of_axes():
    f, r = _fixture_tables()
    spec = plan_liquid_directional_calibration_domain(foundation=f, readiness=r)
    assert spec["contract"] == DOMAIN_CONTRACT
    assert spec["phases"] == ["LIQUID"]
    assert spec["wavelengths_nm"] == list(SIX_BAND_WAVELENGTHS_NM)
    assert min(spec["cot"]) <= 0.5 and max(spec["cot"]) >= 3.0
    assert 10.0 in spec["effective_radius_um"] and 12.0 in spec["effective_radius_um"]
    assert min(spec["solar_zenith_deg"]) <= 89.1 and max(spec["solar_zenith_deg"]) >= 93.9
    assert max(spec["view_zenith_deg"]) > 90.0
    assert max(spec["relative_azimuth_deg"]) == 180.0
    assert spec["grid_design"]["cloud_thickness_is_interpolation_axis"] is False
    assert "cloud_thickness_km" not in spec["interpolation_axes"]
    assert spec["planned_job_count"] > 0


def test_domain_planner_refuses_to_invent_targets_when_no_real_ready_liquid_data():
    f, r = _fixture_tables()
    r["phase"] = "ICE"
    with pytest.raises(ValueError, match="NO_REAL_TIER2_READY_LIQUID_TARGETS"):
        plan_liquid_directional_calibration_domain(foundation=f, readiness=r)


def test_mystic_recipe_and_job_geometry_support_horizon_crossing():
    recipe = build_libradtran_mystic_solver_recipe(libRadtran_version="2.0-test", photons_per_job=200000)
    assert recipe["contract"] == SOLVER_RECIPE_CONTRACT
    assert recipe["solver_family"] == "LIBRADTRAN_UVSPEC_MYSTIC"
    assert recipe["spherical_geometry"] == "mc_spherical 1D"
    assert recipe["multiple_scattering_enabled"] is True
    jobs = build_external_job_table(_tiny_domain(), solver_recipe=recipe)
    assert "response_factor" not in jobs.columns
    assert set(jobs["execution_state"]) == {"PENDING_EXTERNAL_LIBRADTRAN_MYSTIC"}
    # theta_v=92 deg is Cloud->Observer slightly below local horizon; sensor-look umu becomes positive.
    row = jobs[jobs["view_zenith_deg"].eq(92.0)].iloc[0]
    assert math.isclose(float(row["uvspec_umu"]), -math.cos(math.radians(92.0)), rel_tol=0, abs_tol=1e-12)
    assert float(row["uvspec_umu"]) > 0


def test_uvspec_template_is_explicit_external_placeholder_not_fake_lut():
    text = uvspec_template_text()
    assert "rte_solver mystic" in text
    assert "mc_spherical 1D" in text
    assert "mc_vroom" in text
    assert "wc_properties mie interpolate" in text
    assert "<VALIDATED_ATMOSPHERE_PROFILE>" in text
    assert "MUST NOT be interpreted as a completed production LUT" in text


def test_external_bundle_contains_jobs_recipe_template_schema_and_nonproduction_manifest(tmp_path: Path):
    recipe = build_libradtran_mystic_solver_recipe(libRadtran_version="external")
    audit = write_external_calibration_bundle(tmp_path, domain_spec=_tiny_domain(), solver_recipe=recipe)
    assert audit["ok"] is True
    assert audit["production_lut_generated"] is False
    expected = {
        "tier2_liquid_directional_calibration_jobs.csv",
        "tier2_liquid_directional_domain_spec.json",
        "tier2_libradtran_mystic_solver_recipe.json",
        "uvspec_mystic_spherical_template.inp",
        "tier2_external_results_required_schema.csv",
        "tier2_liquid_directional_calibration_bundle_manifest.json",
    }
    assert expected.issubset({p.name for p in tmp_path.iterdir()})
    manifest = json.loads((tmp_path / "tier2_liquid_directional_calibration_bundle_manifest.json").read_text())
    assert manifest["production_lut_state"] == "NOT_YET_GENERATED_EXTERNAL_RT_REQUIRED"
    assert manifest["job_count"] == audit["job_count"]


def test_external_result_qc_rejects_incomplete_high_sigma_and_nonzero_exit():
    recipe = build_libradtran_mystic_solver_recipe()
    jobs = build_external_job_table(_tiny_domain(), solver_recipe=recipe)
    good = _results_for_jobs(jobs)
    assert validate_external_rt_results(jobs, good)["ok"] is True

    incomplete = good.iloc[:-1].copy()
    a = validate_external_rt_results(jobs, incomplete)
    assert a["ok"] is False
    assert any("INCOMPLETE_JOB_SET" in x for x in a["errors"])

    noisy = good.copy()
    noisy.loc[0, "mc_relative_sigma"] = 0.5
    a = validate_external_rt_results(jobs, noisy)
    assert "EXTERNAL_RT_RESULTS_MC_CONVERGENCE_FAILED" in a["errors"]

    failed = good.copy()
    failed.loc[0, "solver_exit_code"] = 1
    a = validate_external_rt_results(jobs, failed)
    assert "EXTERNAL_RT_RESULTS_SOLVER_EXIT_NONZERO" in a["errors"]


def test_external_result_qc_rejects_duplicate_unknown_and_unapproved_solver():
    recipe = build_libradtran_mystic_solver_recipe()
    jobs = build_external_job_table(_tiny_domain(), solver_recipe=recipe)
    good = _results_for_jobs(jobs)
    dup = pd.concat([good, good.iloc[[0]]], ignore_index=True)
    assert "EXTERNAL_RT_RESULTS_DUPLICATE_JOB_ID" in validate_external_rt_results(jobs, dup)["errors"]
    bad = good.copy()
    bad["solver_family"] = "PLANE_PARALLEL_FAKE"
    assert "EXTERNAL_RT_RESULTS_SOLVER_FAMILY_INVALID_OR_MIXED" in validate_external_rt_results(jobs, bad)["errors"]


def test_production_package_can_only_be_built_after_complete_external_qc():
    recipe = build_libradtran_mystic_solver_recipe()
    jobs = build_external_job_table(_tiny_domain(), solver_recipe=recipe)
    results = _results_for_jobs(jobs)
    metadata = {
        "lut_version": "R5.7.23-GENUINE-EXTERNAL-TEST",
        "calibration_id": "EXT-MYSTIC-TEST-001",
        "calibration_source": "LIBRADTRAN MYSTIC external validated run",
        "calibration_date": "2026-09-08",
        "validation_reference": "R5.7.23 deterministic external-result fixture validation",
        "solver_family": "LIBRADTRAN_UVSPEC_MYSTIC",
        "solver_version": "test-external-rt-1",
        "cloud_optics_source": "LIBRADTRAN liquid-water Mie test contract",
        "phase_function_source": "FULL_MIE_PHASE_FUNCTION",
        "multiple_scattering_enabled": True,
        "response_definition": DIRECTIONAL_RESPONSE_DEFINITION,
        "response_units": DIRECTIONAL_RESPONSE_UNITS,
        "geometry_convention": DIRECTIONAL_GEOMETRY_CONVENTION,
        "directional_hemisphere_support": "FULL_0_180",
        "calibration_state": "CALIBRATED",
        "qc_state": "PASS",
        "calibration_contract": DIRECTIONAL_CALIBRATION_CONTRACT,
        "solver_adapter_contract": MYSTIC_ADAPTER_CONTRACT,
        "incident_irradiance_reference": INCIDENT_IRRADIANCE_REFERENCE,
        "atmospheric_coupling": ATMOSPHERIC_COUPLING,
        "surface_boundary": SURFACE_BOUNDARY,
        "reference_cloud_base_km": 5.0,
        "reference_cloud_top_km": 6.0,
        "cloud_vertical_sensitivity_validation_reference": "TEST_VERTICAL_SENSITIVITY_PASS",
        "geometry_mapping_validation_reference": "TEST_GEOMETRY_MAPPING_PASS",
        "minimum_photon_count": 1000000,
        "maximum_mc_relative_error": 0.02,
        "maximum_mc_absolute_error": 0.01,
        "calibration_scope": CALIBRATION_SCOPE,
    }
    csv_bytes, manifest_bytes, audit = build_production_lut_from_external_results(
        jobs=jobs, results=results, metadata=metadata, domain_spec=_tiny_domain(), minimum_photon_count=1000000
    )
    assert audit["ok"] is True
    assert audit["synthetic_response_used"] is False
    manifest = json.loads(manifest_bytes)
    assert manifest["solver_family"] == "LIBRADTRAN_UVSPEC_MYSTIC"
    assert manifest["directional_hemisphere_support"] == "FULL_0_180"
    runtime = validate_directional_lut_bytes(csv_bytes, manifest_bytes)
    assert runtime["ok"] is True

    with pytest.raises(ValueError, match="EXTERNAL_RT_RESULTS_INCOMPLETE_JOB_SET"):
        build_production_lut_from_external_results(
            jobs=jobs, results=results.iloc[:-1], metadata=metadata, domain_spec=_tiny_domain(), minimum_photon_count=1000000
        )
