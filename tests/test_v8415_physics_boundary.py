from pathlib import Path

import numpy as np
import pandas as pd

from firecloud import gas_rt


ROOT = Path(__file__).resolve().parents[1]


def _profile():
    rows = []
    for distance in (0.0, 10.0):
        for altitude in (0.0, 10.0):
            rows.append({
                "point_id": f"p{distance:g}",
                "distance_km": distance,
                "direction_offset_deg": 0.0,
                "altitude_agl_km": altitude,
                "temperature_k": 280.0,
                "pressure_hpa": 500.0,
                "o2_mole_fraction": 0.20946,
                "h2o_mole_fraction": 0.01,
                "o3_mole_fraction": 8e-6,
            })
    return pd.DataFrame(rows)


def test_pressure_profile_boundary_is_clipped_not_reported_as_bracket_missing(monkeypatch):
    targets = pd.DataFrame([{
        "point_id": "target",
        "distance_km": 0.0,
        "direction_offset_deg": 0.0,
        "voxel_center_km": 1.0,
        "geometric_illuminated_fraction": 1.0,
    }])

    def fake_ray(*args, **kwargs):
        # One segment crosses the real 10-km profile top: only half is supported.
        return np.array([[5.0, 15.0]])

    monkeypatch.setattr(gas_rt, "_ray_altitudes_matrix", fake_ray)
    out = gas_rt.integrate_gas_sun_to_targets(targets, _profile(), 0.0)
    row = out.iloc[0]
    assert bool(row["gas_rt_boundary_clipped"])
    assert row["gas_rt_failure_cause"] == ""
    assert str(row["gas_rt_quality"]).startswith("HITRAN_DERIVED_3D_GAS_RT")
    assert np.isfinite(row["gas_tau_o3_600nm"])
    assert np.isfinite(row["o3_transmission_600nm"])


def test_pressure_profile_bottom_exit_is_expected_termination(monkeypatch):
    targets = pd.DataFrame([{
        "point_id": "target",
        "distance_km": 0.0,
        "direction_offset_deg": 0.0,
        "voxel_center_km": 1.0,
        "geometric_illuminated_fraction": 1.0,
    }])

    def fake_ray(*args, **kwargs):
        # The incoming ray crosses the lower edge of the real profile.  Only
        # the supported part is integrated; the below-profile part is not a
        # false vertical-bracket failure.
        return np.array([[5.0, -5.0]])

    monkeypatch.setattr(gas_rt, "_ray_altitudes_matrix", fake_ray)
    out = gas_rt.integrate_gas_sun_to_targets(targets, _profile(), 0.0)
    row = out.iloc[0]
    assert row["gas_rt_failure_cause"] == ""
    assert row["gas_rt_domain_status"] == "MODEL_BOTTOM_TERMINATED"
    assert row["gas_rt_expected_termination"] == "MODEL_BOTTOM"
    assert str(row["gas_rt_quality"]).endswith("MODEL_BOTTOM_TERMINATED")
    assert bool(row["gas_rt_boundary_clipped"])
    assert np.isfinite(row["o3_transmission_600nm"])


def test_575_builder_is_explicitly_configurable_without_changing_runtime_default():
    builder = (ROOT / "build_hitran_band_coefficients.py").read_text(encoding="utf-8")
    assert 'default="600,650,700,750"' in builder
    assert '"--wavelengths"' in builder
    assert "requested_min=min(wavelengths)-12.5" in builder
