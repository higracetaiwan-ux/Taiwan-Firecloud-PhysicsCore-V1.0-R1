import math

import pandas as pd

import firecloud
import firecloud.viewing_spectral as vs


TIME = "2026-09-13T10:00:00Z"
ANGLE = -2.0
DIRECTION = 0.0
KEY = (TIME, ANGLE, DIRECTION)


def _target(distance=10.0, base=4.0, top=5.0):
    return pd.Series({
        "time": TIME,
        "solar_altitude_deg": ANGLE,
        "canvas_id": "canvas::target",
        "cloud_layer_id": "target::cloud",
        "direction_offset_deg": DIRECTION,
        "target_distance_km": distance,
        "target_base_km": base,
        "target_top_km": top,
        "photographic_target_eligible": True,
    })


def _viewing_geometry(target=None):
    t = dict((_target() if target is None else target).to_dict())
    return pd.DataFrame([t])


def _cloud_rows(*, cloud_base=0.2, cloud_top=5.0):
    rows=[]
    for i,d in enumerate((2.0,4.0,6.0)):
        rows.append({
            "time": TIME,
            "solar_altitude_deg": ANGLE,
            "direction_offset_deg": DIRECTION,
            "distance_km": d,
            "layer_id": f"layer_{i}",
            "z_base_km": cloud_base,
            "z_top_km": cloud_top,
            "cloud_fraction": 0.4 + 0.1*i,
            "cot": 0.7 + 0.2*i,
            "evidence_consistency": "CONSISTENT",
        })
    return pd.DataFrame(rows)


def _compare(cloud, target=None, optics=None):
    target = _target() if target is None else target
    optics = pd.DataFrame() if optics is None else optics
    groups = vs._route_group_map(cloud)
    support_cache = {}
    numeric_groups = {}
    numeric_max = {}
    vs._prepare_cloud_numeric_routes_for_targets(
        _viewing_geometry(target), groups, support_cache, numeric_groups, numeric_max
    )
    cotmap = vs._exact_cot_map(cloud, optics)
    truth_map = vs._target_optical_truth_map(optics)
    legacy_diag={}
    prepared_diag={}
    legacy = vs._cloud_expected_tau(
        target, cloud, optics, 6371.0,
        prefiltered_layers=groups.get(KEY), cotmap=cotmap,
        support_cache={}, truth_map=truth_map, diagnostic_sink=legacy_diag,
    )
    prepared = vs._cloud_expected_tau_prepared(
        target, cloud, optics, 6371.0,
        prepared_route=numeric_groups.get(KEY,[]), cotmap=cotmap,
        truth_map=truth_map, diagnostic_sink=prepared_diag,
    )
    return legacy, prepared, legacy_diag, prepared_diag, numeric_groups


def test_version_is_r574134106():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.6"


def test_cloud_numeric_context_resolved_occupancy_is_exact():
    legacy, prepared, legacy_diag, prepared_diag, numeric = _compare(_cloud_rows())
    assert prepared == legacy
    assert prepared_diag == legacy_diag
    assert prepared[2] == "VIEW_CLOUD_OPTICS_RESOLVED_OCCUPANCY_EXPECTATION"
    assert len(numeric[KEY]) == 3


def test_cloud_numeric_context_missing_cot_is_exact_and_fail_closed():
    cloud=_cloud_rows()
    cloud.loc[cloud.index[1],"cot"] = math.nan
    legacy, prepared, legacy_diag, prepared_diag, _ = _compare(cloud)
    assert prepared == legacy
    assert prepared_diag == legacy_diag
    assert prepared[0] is None
    assert prepared[2] == "VIEW_CLOUD_OPTICS_PARTIAL"
    assert prepared_diag["unresolved_blocker_count"] >= 1


def test_cloud_numeric_context_direct_conflict_is_exact():
    cloud=_cloud_rows()
    cloud.loc[cloud.index[1],"cot"] = math.nan
    cloud.loc[cloud.index[1],"evidence_consistency"] = "CF_CLOUD_CONDENSATE_ZERO"
    legacy, prepared, legacy_diag, prepared_diag, _ = _compare(cloud)
    assert prepared == legacy
    assert prepared_diag == legacy_diag
    assert prepared_diag["conflict_blocker_count"] >= 1
    assert "CF_CLOUD_CONDENSATE_ZERO" in prepared_diag["conflict_states"]


def test_cloud_numeric_context_missing_cloud_fraction_is_exact():
    cloud=_cloud_rows()
    cloud.loc[cloud.index[0],"cloud_fraction"] = math.nan
    legacy, prepared, legacy_diag, prepared_diag, _ = _compare(cloud)
    assert prepared == legacy
    assert prepared_diag == legacy_diag
    assert prepared[0] is None
    assert prepared[2] == "VIEW_CLOUD_OPTICS_PARTIAL"


def test_cloud_numeric_context_path_clear_is_exact():
    cloud=_cloud_rows(cloud_base=10.0, cloud_top=12.0)
    legacy, prepared, legacy_diag, prepared_diag, _ = _compare(cloud)
    assert prepared == legacy
    assert prepared_diag == legacy_diag
    assert prepared == (0.0,0.0,"VIEW_CLOUD_PATH_CLEAR",0,"")


def test_cloud_numeric_context_headerless_empty_preserves_missing_not_clear():
    cloud=pd.DataFrame()
    target=_target()
    legacy_diag={}; prepared_diag={}
    legacy=vs._cloud_expected_tau(target,cloud,pd.DataFrame(),6371.0,diagnostic_sink=legacy_diag)
    prepared=vs._cloud_expected_tau_prepared(
        target,cloud,pd.DataFrame(),6371.0,prepared_route=[],cotmap={},truth_map={},diagnostic_sink=prepared_diag
    )
    assert prepared == legacy
    assert prepared_diag == legacy_diag
    assert prepared[0] is None
    assert prepared[2] == "VIEW_CLOUD_VOLUME_UNRESOLVED"


def test_builder_materializes_numeric_cloud_rows_once_in_runtime_context():
    cloud=_cloud_rows()
    target_df=_viewing_geometry()
    aerosol=pd.DataFrame(); gas=pd.DataFrame(); optics=pd.DataFrame()
    ctx=vs.prepare_viewing_spectral_runtime_context(cloud,optics,aerosol,gas)
    stats={}
    out=vs.build_viewing_spectral_extinction(
        target_df,cloud,optics,aerosol,gas,None,runtime_context=ctx,runtime_cache_stats=stats
    )
    assert not out.empty
    assert stats["runtime_context_reused"] is True
    assert stats["cloud_numeric_route_count"] == 1
    assert stats["cloud_numeric_row_count"] == 3
    assert len(ctx["cloud_numeric_groups"][KEY]) == 3
