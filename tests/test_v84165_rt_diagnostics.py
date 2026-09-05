import pandas as pd

from firecloud.model import _build_spectral_coverage_diagnostics


def test_expected_geometry_termination_is_separate_from_true_missing():
    rows = [
        {
            "solar_altitude_deg": -1.0, "direction_offset_deg": 0.0, "distance_km": 20.0,
            "full_spectral_transmission_650nm": 0.8,
            "gas_rt_domain_status": "MODEL_TOP_TERMINATED",
            "gas_rt_expected_termination": "MODEL_TOP",
            "gas_rt_failure_cause": "", "spectral_rt_missing_cause": "",
            "geometric_illuminated_fraction": 1.0,
        },
        {
            "solar_altitude_deg": -1.0, "direction_offset_deg": 0.0, "distance_km": 20.0,
            "full_spectral_transmission_650nm": float("nan"),
            "gas_rt_domain_status": "NOT_APPLICABLE",
            "gas_rt_expected_termination": "EARTH_SHADOW",
            "gas_rt_failure_cause": "EARTH_SHADOW_NO_DIRECT_SOLAR_RAY",
            "spectral_rt_missing_cause": "GAS_EARTH_SHADOW_NO_DIRECT_SOLAR_RAY",
            "geometric_illuminated_fraction": 0.0,
        },
        {
            "solar_altitude_deg": -1.0, "direction_offset_deg": 0.0, "distance_km": 20.0,
            "full_spectral_transmission_650nm": float("nan"),
            "gas_rt_domain_status": "TRUE_ROUTE_DOMAIN_MISSING",
            "gas_rt_expected_termination": "",
            "gas_rt_failure_cause": "DYNAMIC_RT_DOMAIN_EXHAUSTED",
            "spectral_rt_missing_cause": "GAS_DYNAMIC_RT_DOMAIN_EXHAUSTED",
            "geometric_illuminated_fraction": 1.0,
        },
    ]
    out = _build_spectral_coverage_diagnostics(pd.DataFrame(rows))
    row = out.iloc[0]
    assert int(row["expected_geometry_termination_count"]) == 2
    assert int(row["true_missing_count"]) == 1
    assert int(row["applicable_voxel_count"]) == 2
    assert float(row["applicable_full_rt_completeness"]) == 0.5
    assert row["dominant_expected_geometry_termination"] in {"EARTH_SHADOW", "MODEL_TOP"}
    assert row["dominant_missing_cause"] == "DYNAMIC_RT_DOMAIN_EXHAUSTED"


def test_cams_prefetch_is_bounded_unique_time_parallelism():
    src = open("firecloud/model.py", encoding="utf-8").read()
    assert "ThreadPoolExecutor" in src
    assert 'FIRECLOUD_CAMS_PREFETCH_WORKERS' in src
    assert 'min(_cams_parallel_workers, 2' in src
    assert 'PREFETCH_PARALLEL' in src


def test_cams_checkpoint_keeps_role_specific_files_for_parallel_workers():
    src = open("firecloud/providers/cams_native.py", encoding="utf-8").read()
    assert "cams_worker_checkpoint_{safe_role}" in src
    assert "worker_token" in src
    assert "cams_worker_checkpoints.json" in open("app.py", encoding="utf-8").read()
