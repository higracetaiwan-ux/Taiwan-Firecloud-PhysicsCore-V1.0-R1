import pandas as pd
import firecloud
import firecloud.red_light_availability as rla


EXPECTED_RED_LIGHT_COMPONENT_STAGES = [
    "RED_LIGHT_COMPONENT_BUILD_RECEIVERS",
    "RED_LIGHT_COMPONENT_SPECTRAL_RT",
    "RED_LIGHT_COMPONENT_CLOUD_PATH",
    "RED_LIGHT_COMPONENT_VIRTUAL_CANVAS",
    "RED_LIGHT_COMPONENT_PRECIPITATION_PATH",
    "RED_LIGHT_COMPONENT_MERGE",
    "RED_LIGHT_COMPONENT_SIX_BAND_AVAILABILITY",
    "RED_LIGHT_COMPONENT_PATH_STATE",
]


def _receiver():
    return pd.DataFrame([{
        "reference_receiver_id": "redref::test",
        "reference_domain": "PRIMARY_CANVAS_0_40",
        "reference_cloud_base_km": 5.0,
        "sampled_receiver_altitude_km": 5.0,
        "direction_offset_deg": 0.0,
        "distance_km": 20.0,
        "v1_direct_solar_fraction": 1.0,
        "point_id": "P",
        "solar_altitude_deg": -2.0,
    }])


def _install_deterministic_fakes(monkeypatch):
    receiver = _receiver()

    monkeypatch.setattr(
        rla, "build_reference_receiver_targets",
        lambda *args, **kwargs: receiver.copy(),
    )

    def fake_spectral(receivers, *args, **kwargs):
        out = receivers.copy()
        out["gas_path_completeness"] = 1.0
        out["gas_rt_domain_status"] = "IN_DOMAIN"
        out["gas_rt_quality"] = "HITRAN_DERIVED_3D_GAS_RT_TEST"
        out["aerosol_rt_path_complete"] = True
        out["aerosol_rt_temporal_evidence_state"] = "EXACT_VALID_TIME"
        for wl in rla.SIX_BAND_WAVELENGTHS_NM:
            out[f"rayleigh_transmission_{wl}nm"] = 1.0
            out[f"aerosol_transmission_{wl}nm"] = 1.0
            out[f"gas_transmission_{wl}nm"] = 1.0
        return out

    monkeypatch.setattr(rla, "build_spectral_rt", fake_spectral)

    def fake_cloud(scene, receivers, *args, **kwargs):
        keys = [
            "reference_receiver_id", "direction_offset_deg", "distance_km",
            "reference_cloud_base_km", "sampled_receiver_altitude_km",
        ]
        out = receivers[keys].copy()
        out["cloud_path_evidence_state"] = "FULL"
        out["resolved_upstream_cloud_transmission"] = 1.0
        out["upstream_cloud_intersection_count"] = 0
        out["cloud_geometry_completeness"] = 1.0
        return out

    monkeypatch.setattr(rla, "build_reference_receiver_cloud_path_evidence", fake_cloud)

    def fake_precip(canvases, *args, **kwargs):
        out = pd.DataFrame([{
            "canvas_id": "redref::test",
            "status": "FULL",
            "optical_evidence": "FULL",
            "hydrometeor_intersection_count": 0,
            "hydrometeor_unresolved_intersection_count": 0,
            "native_hydrometeor_field_completeness": 1.0,
        }])
        for wl in rla.SIX_BAND_WAVELENGTHS_NM:
            out[f"tau_precip_{wl}nm"] = 0.0
        return out

    monkeypatch.setattr(rla, "build_precipitation_path_evidence", fake_precip)


def _call(profile=None):
    return rla.build_red_light_reference_evidence(
        native_optical_voxels=pd.DataFrame([{"x": 1}]),
        scene=None,
        route_snapshot=pd.DataFrame(),
        aerosol_spectral_snapshot=pd.DataFrame(),
        cams_native_aerosol_snapshot=pd.DataFrame(),
        gas_profile=pd.DataFrame(),
        solar_altitude_deg=-2.0,
        earth_radius_km=6371.0,
        valid_time="T",
        runtime_profile_rows=profile,
    )


def test_version_r5741349():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.9"


def test_red_light_profiler_emits_all_eight_components_without_changing_science_output(monkeypatch):
    _install_deterministic_fakes(monkeypatch)
    baseline = _call()
    rows = []
    profiled = _call(rows)
    pd.testing.assert_frame_equal(profiled, baseline, check_dtype=True, check_exact=True)
    assert [r["stage"] for r in rows] == EXPECTED_RED_LIGHT_COMPONENT_STAGES
    assert all(float(r["elapsed_seconds"]) >= 0.0 for r in rows)
    assert all("R5741349_COMPONENT_PROFILE_ONLY" in str(r.get("detail", "")) for r in rows)


def test_model_exports_red_light_component_rows_to_performance_diagnostics():
    src = (rla.__file__.replace("red_light_availability.py", "model.py"))
    text = open(src, encoding="utf-8").read()
    for stage in EXPECTED_RED_LIGHT_COMPONENT_STAGES:
        # The exact stage literal lives in red_light_availability.py; model must
        # forward the returned stage into performance_rows under the diagnostic marker.
        assert stage in open(rla.__file__, encoding="utf-8").read()
    assert '"cache_status": "R5741349_COMPONENT_PROFILE_ONLY"' in text
    assert "runtime_profile_rows=_red_ref_component_profile" in text
