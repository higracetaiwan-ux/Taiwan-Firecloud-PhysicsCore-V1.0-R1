import io
import json
import math

import pandas as pd
import pytest

from firecloud.contracts import CloudScene
from firecloud.tier2_scattering_calibration import (
    CALIBRATION_CONTRACT,
    GEOMETRY_CONVENTION,
    RESPONSE_DEFINITION,
    RESPONSE_UNITS,
    build_calibration_jobs,
    build_calibration_package,
    validate_calibration_metadata,
)
from firecloud.tier2_scattering_runtime import validate_scattering_lut_bytes
from firecloud.tier2_scattering_solver import (
    build_tier2_scattering_response,
    interpolate_response_factor,
    mark_domain_interpolation_execution,
    summarize_tier2_scattering_response,
)
from firecloud.v1_runtime import CANVAS_CANDIDATE_TABLE_COLUMNS, build_r2_geometry_tables

WLS = [550, 575, 600, 650, 700, 750]


def response_formula(wl, cot, reff, thick, angle):
    return 0.01 + wl / 100000.0 + 0.02 * cot + 0.001 * reff + 0.003 * thick + 0.0001 * angle


def full_samples():
    rows = []
    for wl in WLS:
        for cot in [1.0, 3.0]:
            for reff in [8.0, 12.0]:
                for thick in [0.5, 1.5]:
                    for angle in [60.0, 120.0]:
                        rows.append({
                            "phase": "LIQUID",
                            "wavelength_nm": wl,
                            "cot": cot,
                            "effective_radius_um": reff,
                            "cloud_thickness_km": thick,
                            "scattering_angle_deg": angle,
                            "response_factor": response_formula(wl, cot, reff, thick, angle),
                        })
    return pd.DataFrame(rows)


def production_metadata():
    return {
        "calibration_contract": CALIBRATION_CONTRACT,
        "calibration_state": "CALIBRATED",
        "calibration_id": "CAL-PHYS-001",
        "calibration_source": "LIBRADTRAN_VALIDATED_PHYSICAL_RT_GRID",
        "calibration_date": "2026-09-07",
        "qc_state": "PASS",
        "solver_family": "LIBRADTRAN_UVSPEC_DISORT",
        "solver_version": "3.x-test-provenance",
        "cloud_optics_source": "VALIDATED_MIE_WATER_TABLES",
        "phase_function_source": "VALIDATED_MIE_PHASE_FUNCTION",
        "multiple_scattering_enabled": True,
        "response_definition": RESPONSE_DEFINITION,
        "response_units": RESPONSE_UNITS,
        "geometry_convention": GEOMETRY_CONVENTION,
        "validation_reference": "UNIT_TEST_PHYSICAL_PROVENANCE_PLACEHOLDER_REFERENCE",
        "lut_version": "TEST20",
    }


def package():
    csv_bytes, manifest_bytes, _ = build_calibration_package(full_samples(), production_metadata())
    audit = validate_scattering_lut_bytes(csv_bytes, manifest_bytes)
    assert audit["ok"], audit
    assert audit["solver_eligible"] is True
    lut = pd.read_csv(io.BytesIO(csv_bytes))
    return lut, audit


def exact_domain():
    return pd.DataFrame([{
        "time": "t", "solar_altitude_deg": -2.0, "canvas_id": "c1", "cloud_layer_id": "l1",
        "operational_domain": "PRIMARY_CANVAS_0_40", "distance_km": 20.0,
        "target_optical_truth_state": "EXACT_PRIMARY_NATIVE", "target_cot_semantics": "EXACT_VALUE",
        "phase": "LIQUID", "cot_lower_bound": 2.0, "cot_upper_bound": 2.0,
        "effective_radius_um": 10.0, "cloud_thickness_km": 1.0, "scattering_angle_deg": 90.0,
        "lut_runtime_state": "CALIBRATED_LUT_RUNTIME_READY", "lut_version": "TEST20", "calibration_id": "CAL-PHYS-001",
        "interpolation_domain_state": "INTERPOLATION_DOMAIN_READY_DETERMINISTIC",
        "deterministic_interpolation_eligible": True, "bounded_interpolation_eligible": False,
        "interpolation_executed": False,
    }])


def bounded_domain():
    d = exact_domain().copy()
    d.loc[0, "target_optical_truth_state"] = "BOUNDED_NATIVE_BRACKET"
    d.loc[0, "target_cot_semantics"] = "BOUNDED_INTERVAL"
    d.loc[0, "cot_lower_bound"] = 1.2
    d.loc[0, "cot_upper_bound"] = 2.8
    d.loc[0, "interpolation_domain_state"] = "INTERPOLATION_DOMAIN_READY_BOUNDED"
    d.loc[0, "deterministic_interpolation_eligible"] = False
    d.loc[0, "bounded_interpolation_eligible"] = True
    return d


def illumination(value=2.0):
    row = {"canvas_id": "c1"}
    for wl in WLS:
        row[f"relative_base_illumination_{wl}nm"] = value
    return pd.DataFrame([row])


def test_synthetic_or_regression_calibration_source_cannot_be_solver_eligible():
    m = production_metadata()
    m["calibration_source"] = "SYNTHETIC_REGRESSION_ONLY"
    a = validate_calibration_metadata(m)
    assert not a["ok"]
    assert "CALIBRATION_SYNTHETIC_SOURCE_NOT_PRODUCTION_ELIGIBLE" in a["errors"]


def test_calibration_job_generator_emits_no_fabricated_response_values():
    spec = {
        "phases": ["LIQUID", "ICE"], "wavelengths_nm": WLS,
        "cot": [1, 3], "effective_radius_um": [10],
        "cloud_thickness_km": [1], "scattering_angle_deg": [60, 120],
    }
    jobs = build_calibration_jobs(spec, solver_family="LIBRADTRAN_UVSPEC_DISORT")
    assert len(jobs) == 2 * 6 * 2 * 1 * 1 * 2
    assert "response_factor" not in jobs.columns
    assert jobs["calibration_state"].eq("PENDING_EXTERNAL_RT").all()


def test_calibration_package_requires_complete_tensor_grid():
    q = full_samples().iloc[:-1].copy()
    with pytest.raises(ValueError, match="CALIBRATION_TENSOR_GRID_INCOMPLETE"):
        build_calibration_package(q, production_metadata())


def test_production_package_sets_second_solver_gate():
    _, audit = package()
    assert audit["production_calibration_state"] == "PRODUCTION_CALIBRATION_READY"
    assert audit["solver_family"] == "LIBRADTRAN_UVSPEC_DISORT"
    assert audit["response_definition"] == RESPONSE_DEFINITION
    assert audit["response_units"] == RESPONSE_UNITS


def test_4d_multilinear_solver_reproduces_linear_calibration_function():
    lut, _ = package()
    for wl in WLS:
        got = interpolate_response_factor(
            lut, phase="LIQUID", wavelength_nm=wl, cot=2.0,
            effective_radius_um=10.0, cloud_thickness_km=1.0, scattering_angle_deg=90.0,
        )
        expected = response_formula(wl, 2.0, 10.0, 1.0, 90.0)
        assert got == pytest.approx(expected, rel=0, abs=1e-12)


def test_exact_target_executes_six_band_tier2_response_only_with_production_gate():
    lut, audit = package()
    out = build_tier2_scattering_response(
        domain=exact_domain(), calibrated_lut=lut, lut_audit=audit,
        cloud_base_illumination=illumination(2.0),
    )
    r = out.iloc[0]
    assert r.solver_execution_state == "EXECUTED_DETERMINISTIC"
    assert r.response_state == "READY_TIER2_CALIBRATED_LUT"
    assert bool(r.interpolation_executed)
    for wl in WLS:
        expected_factor = response_formula(wl, 2.0, 10.0, 1.0, 90.0)
        assert r[f"response_factor_{wl}nm"] == pytest.approx(expected_factor, abs=1e-12)
        assert r[f"response_factor_{wl}nm_lower_bound"] == pytest.approx(expected_factor, abs=1e-12)
        assert r[f"response_factor_{wl}nm_upper_bound"] == pytest.approx(expected_factor, abs=1e-12)
        assert r[f"tier2_radiance_{wl}nm"] == pytest.approx(2.0 * expected_factor, abs=1e-12)
    assert math.isfinite(float(r.brightness))
    assert math.isfinite(float(r.redness))
    s = summarize_tier2_scattering_response(out).iloc[0]
    assert s.closure_state == "TIER2_RESPONSE_AVAILABLE"
    assert s.deterministic_response_count == 1
    marked = mark_domain_interpolation_execution(exact_domain(), out)
    assert bool(marked.iloc[0].interpolation_executed)


def test_bounded_cot_returns_only_response_envelope_not_nominal():
    lut, audit = package()
    out = build_tier2_scattering_response(
        domain=bounded_domain(), calibrated_lut=lut, lut_audit=audit,
        cloud_base_illumination=illumination(1.0),
    )
    r = out.iloc[0]
    assert r.solver_execution_state == "EXECUTED_BOUNDED_INTERVAL"
    assert r.response_state == "BOUNDED_TIER2_RESPONSE_AVAILABLE"
    assert pd.isna(r["response_factor_600nm"])
    assert pd.isna(r["tier2_radiance_600nm"])
    expected_lo = response_formula(600, 1.2, 10.0, 1.0, 90.0)
    expected_hi = response_formula(600, 2.8, 10.0, 1.0, 90.0)
    assert r["response_factor_600nm_lower_bound"] == pytest.approx(expected_lo, abs=1e-12)
    assert r["response_factor_600nm_upper_bound"] == pytest.approx(expected_hi, abs=1e-12)
    assert pd.isna(r.brightness)
    assert math.isfinite(float(r.brightness_lower_bound))
    assert math.isfinite(float(r.brightness_upper_bound))


def test_legacy_r5719_schema_only_audit_cannot_execute_solver():
    lut, audit = package()
    legacy = dict(audit)
    legacy["solver_eligible"] = False
    legacy["production_calibration_state"] = "PRODUCTION_CALIBRATION_CONTRACT_NOT_PRESENT"
    out = build_tier2_scattering_response(
        domain=exact_domain(), calibrated_lut=lut, lut_audit=legacy,
        cloud_base_illumination=illumination(),
    )
    r = out.iloc[0]
    assert r.solver_execution_state == "NOT_EXECUTED_PRODUCTION_CALIBRATION_BLOCKED"
    assert not bool(r.interpolation_executed)
    assert pd.isna(r["tier2_radiance_600nm"])


def test_no_canvas_table_keeps_fixed_schema(monkeypatch):
    import firecloud.v1_runtime as vr
    monkeypatch.setattr(
        vr, "build_cloud_scene_from_native_route",
        lambda *a, **k: CloudScene(valid_time=None, layers=(), geometry_completeness=1.0, optics_completeness=1.0),
    )
    out = build_r2_geometry_tables(
        pd.DataFrame(), [], observer_lat=24.0, observer_lon=121.0,
        solar_altitude_deg=-2.0, solar_azimuth_deg=270.0,
        earth_radius_km=6371.0, route_end_km=440.0, route_step_km=20.0,
    )
    assert out["canvases"].empty
    assert list(out["canvases"].columns) == CANVAS_CANDIDATE_TABLE_COLUMNS
