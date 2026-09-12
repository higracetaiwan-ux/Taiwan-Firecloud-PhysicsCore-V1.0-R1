import math
import pandas as pd

from firecloud.contracts import SIX_BAND_WAVELENGTHS_NM
import firecloud.viewing_spectral as viewing_spectral


def _target():
    return {
        "time": "2026-08-30T18:00:00+08:00",
        "solar_altitude_deg": -1.0,
        "canvas_id": "hist-canvas",
        "cloud_layer_id": "hist-layer",
        "direction_offset_deg": 0.0,
        "target_distance_km": 20.0,
        "target_base_km": 5.0,
        "target_top_km": 7.0,
        "photographic_target_eligible": True,
    }


def _precip():
    row={
        "time": _target()["time"],
        "solar_altitude_deg": -1.0,
        "canvas_id": "hist-canvas",
        "view_precipitation_status": "VIEW_PRECIPITATION_OPTICS_RESOLVED",
    }
    for wl in SIX_BAND_WAVELENGTHS_NM:
        row[f"view_tau_precip_{int(wl)}nm"] = 0.0
    return pd.DataFrame([row])


def _resolve_noncloud_components(monkeypatch):
    tau={int(w):0.01 for w in SIX_BAND_WAVELENGTHS_NM}
    monkeypatch.setattr(
        viewing_spectral,
        "_integrate_view_aerosol",
        lambda *a, **k: (tau.copy(), "VIEW_AEROSOL_3D_RESOLVED", 20.0, {
            "required_segment_count":1,
            "resolved_segment_count":1,
            "temporal_fallback_segment_count":0,
            "temporal_missing_segment_count":0,
            "lowest_endpoint_snap_segment_count":0,
        }),
    )
    monkeypatch.setattr(
        viewing_spectral,
        "_integrate_view_gas",
        lambda *a, **k: (tau.copy(), "VIEW_GAS_RT_RESOLVED", 20.0),
    )


def test_headerless_empty_cloud_volume_fails_closed_instead_of_keyerror():
    tau,conditional,status,blockers,src = viewing_spectral._cloud_expected_tau(
        pd.Series(_target()), pd.DataFrame(), pd.DataFrame(), 6371.0
    )
    assert tau is None
    assert conditional == 0.0
    assert status == "VIEW_CLOUD_VOLUME_UNRESOLVED"
    assert blockers == 0
    assert src == ""


def test_missing_direction_schema_fails_closed_instead_of_keyerror():
    malformed = pd.DataFrame([{
        "distance_km": 10.0,
        "z_base_km": 1.0,
        "z_top_km": 2.0,
    }])
    tau,_,status,blockers,_ = viewing_spectral._cloud_expected_tau(
        pd.Series(_target()), malformed, pd.DataFrame(), 6371.0
    )
    assert tau is None
    assert status == "VIEW_CLOUD_VOLUME_UNRESOLVED"
    assert blockers == 0


def test_full_viewing_builder_survives_historical_empty_cloud_frame(monkeypatch):
    _resolve_noncloud_components(monkeypatch)
    detail = viewing_spectral.build_viewing_spectral_extinction(
        pd.DataFrame([_target()]),
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame(),
        _precip(),
    )
    assert len(detail) == 1
    row=detail.iloc[0]
    assert row["view_cloud_status"] == "VIEW_CLOUD_VOLUME_UNRESOLVED"
    assert row["viewing_spectral_status"] == "VIEW_PARTIAL_SIX_BAND_RT"
    assert "CLOUD" in row["viewing_missing_components"]
    for wl in SIX_BAND_WAVELENGTHS_NM:
        assert pd.isna(row[f"view_tau_cloud_{int(wl)}nm"])
        assert pd.isna(row[f"view_tau_total_{int(wl)}nm"])
        assert pd.isna(row[f"view_transmission_{int(wl)}nm"])


def test_valid_cloud_schema_with_no_matching_route_remains_clear(monkeypatch):
    _resolve_noncloud_components(monkeypatch)
    # Valid cloud evidence exists, but only on +5 deg; target is centerline.
    clouds=pd.DataFrame([{
        "time": _target()["time"],
        "solar_altitude_deg": -1.0,
        "direction_offset_deg": 5.0,
        "distance_km": 10.0,
        "z_base_km": 1.0,
        "z_top_km": 2.0,
        "cloud_fraction": 0.5,
        "layer_id": "other-route",
        "cot": 1.0,
        "evidence_consistency": "CONSISTENT",
    }])
    detail=viewing_spectral.build_viewing_spectral_extinction(
        pd.DataFrame([_target()]), clouds, pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), _precip()
    )
    row=detail.iloc[0]
    assert row["view_cloud_status"] == "VIEW_CLOUD_PATH_CLEAR"
    assert row["view_tau_cloud_650nm"] == 0.0
    assert math.isfinite(float(row["view_tau_total_650nm"]))
