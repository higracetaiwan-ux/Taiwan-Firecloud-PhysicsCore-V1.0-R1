import math

import numpy as np
import pandas as pd

from firecloud.canvas_vertical_microphysics_overlap import (
    OVERLAP_CONTRACT,
    build_canvas_vertical_microphysics_overlap,
    estimate_cot_assumed_reff_from_samples,
)
from firecloud.case_integrity import build_analysis_integrity_audit
from firecloud.contracts import (
    CanvasCandidate, CanvasDomain, CloudFractionState, CloudLayer, CloudScene,
    EvidenceState, GeometryConfidence,
)


def _scene():
    layer = CloudLayer(
        layer_id="L1", direction_offset_deg=0.0, distance_km=10.0,
        z_base_km=12.55, z_top_km=14.35,
        cloud_fraction_state=CloudFractionState.CLOUD_OCCUPIED,
        cloud_fraction=0.5, geometry_confidence=GeometryConfidence.HIGH,
        optical_evidence=EvidenceState.GEOMETRY_ONLY,
        evidence_consistency="CF_CLOUD_CONDENSATE_ZERO",
    )
    canvas = CanvasCandidate(
        canvas_id="C1", cloud_layer_id="L1", latitude=24.0, longitude=121.0,
        cloud_base_altitude_km=12.55, distance_km=10.0, azimuth_deg=270.0,
        operational_domain=CanvasDomain.PRIMARY_CANVAS_0_40,
        geometry_confidence=GeometryConfidence.HIGH,
    )
    return CloudScene(None, (layer,)), (canvas,)


def _primary(q200=2.6e-7, q150=0.0):
    # 150 hPa is a direct CF/cloud-condensate-zero conflict at the target top;
    # 200 hPa lies exactly at the target base.
    return pd.DataFrame([{
        "direction_offset_deg": 0.0, "distance_km": 10.0,
        "model_surface_elevation_m": 0.0,
        "geopotential_height_200hPa": 12550.0,
        "cloud_fraction_200hPa": 0.5,
        "cloud_liquid_water_kgkg_200hPa": 0.0,
        "cloud_ice_water_kgkg_200hPa": q200,
        "temperature_200hPa": 218.0,
        "relative_humidity_200hPa": 80.0,
        "geopotential_height_150hPa": 14350.0,
        "cloud_fraction_150hPa": 0.5,
        "cloud_liquid_water_kgkg_150hPa": 0.0,
        "cloud_ice_water_kgkg_150hPa": q150,
        "temperature_150hPa": 214.0,
        "relative_humidity_150hPa": 70.0,
        "geopotential_height_100hPa": 16750.0,
        "cloud_fraction_100hPa": 0.0,
        "cloud_liquid_water_kgkg_100hPa": 0.0,
        "cloud_ice_water_kgkg_100hPa": 0.0,
        "temperature_100hPa": 210.0,
        "relative_humidity_100hPa": 40.0,
    }])


def _supp(q175=0.0, missing=False):
    return pd.DataFrame([{
        "direction_offset_deg": 0.0, "distance_km": 10.0,
        "surface_elevation_m": 0.0,
        "geopotential_height_m_175hPa": 13400.0,
        "temperature_k_175hPa": 216.0,
        "cloud_liquid_water_kgkg_175hPa": np.nan if missing else 0.0,
        "cloud_ice_water_kgkg_175hPa": np.nan if missing else q175,
        "geopotential_height_m_125hPa": 15440.0,
        "temperature_k_125hPa": 212.0,
        "cloud_liquid_water_kgkg_125hPa": 0.0,
        "cloud_ice_water_kgkg_125hPa": 0.0,
    }])


def _run(primary=None, supp=None):
    scene, canvases = _scene()
    return build_canvas_vertical_microphysics_overlap(
        scene, canvases, primary if primary is not None else _primary(),
        supp if supp is not None else _supp(),
        valid_time="t", solar_altitude_deg=-2.0,
        primary_pressure_levels_hpa=(200, 150, 100),
    )


def test_boundary_positive_is_not_interior_support_and_conflict_blocks_cot():
    overlap, samples = _run()
    assert len(overlap) == 1
    r = overlap.iloc[0]
    assert r.target_vertical_overlap_state == "BOUNDARY_ONLY_NATIVE_CONDENSATE_SUPPORT"
    assert r.native_condensate_positive_boundary_count == 1
    assert r.native_condensate_positive_inside_count == 0
    assert bool(r.direct_target_evidence_conflict)
    assert r.cot_diagnostic_state == "BLOCKED_DIRECT_EVIDENCE_CONFLICT"
    assert pd.isna(r.cot_estimate_assumed_reff)
    assert not bool(r.cot_promotion_allowed)
    assert not bool(r.formation_promotion_allowed)
    pos = samples[samples.positive_native_condensate]
    assert set(pos.sample_target_position) == {"BOUNDARY_LOWER"}


def test_interior_positive_is_mixed_conflict_with_interior_support():
    overlap, _ = _run(supp=_supp(q175=4.0e-7))
    r = overlap.iloc[0]
    assert r.target_vertical_overlap_state == "MIXED_CONFLICT_WITH_INTERIOR_SUPPORT"
    assert r.native_condensate_positive_inside_count == 1
    assert r.native_condensate_positive_boundary_count == 1
    assert r.cot_diagnostic_state == "BLOCKED_DIRECT_EVIDENCE_CONFLICT"


def test_missing_interior_remains_incomplete_not_zero():
    overlap, samples = _run(supp=_supp(missing=True))
    r = overlap.iloc[0]
    assert r.target_vertical_overlap_state == "VERTICAL_EVIDENCE_INCOMPLETE"
    assert r.native_condensate_missing_count_inside_target == 1
    interior = samples[samples.strict_interior]
    assert set(interior.sample_condensate_state) == {"MISSING"}


def test_no_positive_support_classifies_no_native_support():
    overlap, _ = _run(primary=_primary(q200=0.0), supp=_supp(q175=0.0))
    r = overlap.iloc[0]
    assert r.target_vertical_overlap_state == "NO_NATIVE_CONDENSATE_SUPPORT"
    assert r.native_condensate_positive_inside_count == 0
    assert r.native_condensate_positive_boundary_count == 0


def test_cot_scaffold_is_assumed_reff_and_never_claims_native_cot():
    samples = [
        {"pressure_hpa": 700.0, "altitude_agl_km": 3.0, "temperature_k": 275.0,
         "cloud_liquid_water_kgkg": 2e-4, "cloud_ice_water_kgkg": 0.0},
        {"pressure_hpa": 600.0, "altitude_agl_km": 4.0, "temperature_k": 268.0,
         "cloud_liquid_water_kgkg": 1e-4, "cloud_ice_water_kgkg": 0.0},
    ]
    out = estimate_cot_assumed_reff_from_samples(samples, z_base_km=3.0, z_top_km=4.0)
    assert out["cot_diagnostic_state"] == "COT_ESTIMATE_ASSUMED_REFF"
    assert math.isfinite(out["cot_estimate_assumed_reff"])
    assert out["cot_estimate_assumed_reff"] > 0
    assert out["cot_semantics"] == "DIAGNOSTIC_ASSUMED_REFF_NOT_NATIVE_COT"


def test_integrity_guard_enforces_no_promotion_and_boundary_semantics():
    overlap, samples = _run()
    result = {
        "canvas_vertical_microphysics_overlap_required": True,
        "v1_target_canvas_optical_evidence": pd.DataFrame([{
            "canvas_id": "C1", "evidence_consistency": "CF_CLOUD_CONDENSATE_ZERO",
            "target_optical_truth_state": "DIRECT_EVIDENCE_CONFLICT",
        }]),
        "v1_canvas_vertical_microphysics_overlap": overlap,
        "v1_canvas_vertical_microphysics_samples": samples,
        "v1_canvas_vertical_microphysics_overlap_summary": pd.DataFrame([{
            "time": "t", "solar_altitude_deg": -2.0, "canvas_count": 1,
            "overlap_contract": OVERLAP_CONTRACT,
        }]),
    }
    audit = build_analysis_integrity_audit(result)
    row = audit[audit.check_id.eq("CANVAS_VERTICAL_MICROPHYSICS_OVERLAP")].iloc[0]
    assert row.status == "PASS", row.detail

def test_absent_pgrb2b_context_is_missing_not_zero_support():
    overlap, _ = _run(supp=pd.DataFrame())
    r = overlap.iloc[0]
    assert r.expected_supplement_level_count == 1
    assert r.expected_supplement_missing_count == 1
    assert r.target_vertical_overlap_state == "VERTICAL_EVIDENCE_INCOMPLETE"
