from datetime import datetime, timezone

import numpy as np
import pandas as pd

from firecloud.aerosol_physics import (
    apply_real_temporal_spectral_aod_fallback,
    derive_route_spectral_aod,
)
from firecloud.red_light_availability import summarize_red_light_availability


def _snapshot(values, native_marker):
    rows = []
    for point_id, aod550, aod645, aod670, aod800 in values:
        rows.append({
            "point_id": point_id,
            "distance_km": 0.0 if point_id == "p0" else 5.0,
            "direction_offset_deg": 0.0,
            "aod550": aod550,
            "aod645": aod645,
            "aod670": aod670,
            "aod800": aod800,
            "cams_aerext532_m1_1000hPa": native_marker,
            "cams_ozone_kgkg_1000hPa": native_marker * 10.0,
        })
    return pd.DataFrame(rows)


def test_real_one_sided_temporal_fallback_fills_only_spectral_columns_by_point_id():
    target = _snapshot([
        ("p0", np.nan, np.nan, np.nan, np.nan),
        ("p1", np.nan, np.nan, np.nan, np.nan),
    ], native_marker=1.0)
    source = _snapshot([
        ("p1", 0.21, 0.18, 0.17, 0.13),
        ("p0", 0.11, 0.09, 0.08, 0.06),
    ], native_marker=9.0)
    out, meta = apply_real_temporal_spectral_aod_fallback(
        target,
        target_valid_time=datetime(2026, 9, 8, 9, tzinfo=timezone.utc),
        candidate_snapshots=[
            (datetime(2026, 9, 8, 9, tzinfo=timezone.utc), target),
            (datetime(2026, 9, 8, 12, tzinfo=timezone.utc), source),
        ],
    )

    assert meta["state"] == "REAL_ONE_SIDED_TEMPORAL_FALLBACK"
    assert meta["time_offset_hours"] == 3.0
    assert out.set_index("point_id").loc["p0", "aod550"] == 0.11
    assert out.set_index("point_id").loc["p1", "aod550"] == 0.21
    assert out["cams_aerext532_m1_1000hPa"].eq(1.0).all()
    assert out["cams_ozone_kgkg_1000hPa"].eq(10.0).all()
    assert out["spectral_aod_temporal_evidence_state"].eq("REAL_ONE_SIDED_TEMPORAL_FALLBACK").all()
    derived = derive_route_spectral_aod(out)
    assert derived["spectral_aod_quality"].eq(
        "REAL_MULTI_WAVELENGTH_COLUMN_AOD;REAL_ONE_SIDED_TEMPORAL_FALLBACK"
    ).all()


def test_temporal_fallback_never_exceeds_native_three_hour_bound():
    target = _snapshot([("p0", np.nan, np.nan, np.nan, np.nan)], native_marker=1.0)
    source = _snapshot([("p0", 0.11, 0.09, 0.08, 0.06)], native_marker=9.0)
    out, meta = apply_real_temporal_spectral_aod_fallback(
        target,
        target_valid_time="2026-09-08T09:00:00Z",
        candidate_snapshots=[("2026-09-08T15:00:00Z", source)],
    )
    assert meta["state"] == "MISSING"
    assert out["aod550"].isna().all()
    assert out["spectral_aod_temporal_evidence_state"].eq("MISSING").all()


def test_red_light_summary_separates_cloud_conflict_from_aerosol_temporal_state():
    reference = pd.DataFrame([
        {
            "time": "t", "solar_altitude_deg": -2.0,
            "reference_domain": "PRIMARY_CANVAS_0_40",
            "v1_direct_solar_fraction": 1.0,
            "red_light_path_state": "RED_LIGHT_PATH_CONFLICT",
            "red_band_mean_availability": np.nan,
            "red_light_cloud_evidence_state": "DIRECT_EVIDENCE_CONFLICT",
            "red_light_aerosol_evidence_state": "FULL_REAL_ONE_SIDED_TEMPORAL_FALLBACK",
            "red_light_path_evidence_complete": False,
            "cloud_geometry_completeness": 1.0,
        },
        {
            "time": "t", "solar_altitude_deg": -2.0,
            "reference_domain": "EXTENDED_CANVAS_40_100",
            "v1_direct_solar_fraction": 1.0,
            "red_light_path_state": "RED_LIGHT_PATH_UNKNOWN",
            "red_band_mean_availability": np.nan,
            "red_light_cloud_evidence_state": "FULL",
            "red_light_aerosol_evidence_state": "MISSING_OR_PARTIAL",
            "red_light_path_evidence_complete": False,
            "cloud_geometry_completeness": 1.0,
        },
    ])
    out = summarize_red_light_availability(reference).iloc[0]
    assert out["primary_red_light_cloud_evidence_state"] == "DIRECT_EVIDENCE_CONFLICT"
    assert out["primary_red_light_aerosol_evidence_state"] == "FULL_REAL_ONE_SIDED_TEMPORAL_FALLBACK"
    assert out["extended_red_light_cloud_evidence_state"] == "FULL"
    assert out["extended_red_light_aerosol_evidence_state"] == "MISSING_OR_PARTIAL"
    assert out["primary_cloud_conflict_reference_count"] == 1
    assert out["extended_aerosol_missing_reference_count"] == 1
