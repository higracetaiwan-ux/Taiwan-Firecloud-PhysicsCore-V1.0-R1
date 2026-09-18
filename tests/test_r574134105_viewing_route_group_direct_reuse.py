import pandas as pd
import firecloud
import firecloud.viewing_spectral as vs


def _target():
    return pd.DataFrame([{
        "time":"2026-09-13T10:00:00Z",
        "solar_altitude_deg":-2.0,
        "canvas_id":"glow::target",
        "cloud_layer_id":"glow::target",
        "direction_offset_deg":0.0,
        "target_distance_km":5.0,
        "target_base_km":3.0,
        "target_top_km":4.0,
        "photographic_target_eligible":True,
    }])


def _route():
    return pd.DataFrame([
        {"time":"2026-09-13T10:00:00Z","solar_altitude_deg":-2.0,"direction_offset_deg":0.0,"distance_km":0.0},
        {"time":"2026-09-13T10:00:00Z","solar_altitude_deg":-2.0,"direction_offset_deg":0.0,"distance_km":5.0},
        {"time":"2026-09-13T10:00:00Z","solar_altitude_deg":-2.0,"direction_offset_deg":0.0,"distance_km":10.0},
    ])


def _zero_tau():
    return {w:0.0 for w in (550,575,600,650,700,750)}


def test_version_is_r574134105():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.30.1"


def test_builder_passes_full_exact_route_group_without_per_target_slice(monkeypatch):
    targets=_target(); aerosol=_route(); gas=_route(); cloud=pd.DataFrame(); optics=pd.DataFrame()
    key=("2026-09-13T10:00:00Z",-2.0,0.0)
    ids={"cloud_layers":id(cloud),"target_optics":id(optics),"aerosol_snapshots":id(aerosol),"gas_profiles":id(gas)}
    ctx={
        "source_ids":ids,
        "aerosol_groups":{key:aerosol},
        "aerosol_numeric_groups":{},  # force legacy aerosol integrator so its DataFrame input is observable
        "gas_groups":{key:gas},
        "cloud_groups":{},
        "gas_contexts":{key:object()},
        "gas_lut_signatures":{key:"dummy"},
        "gas_sigma_cache":{},
        "cotmap":{},
        "truth_map":{},
        "cloud_support_caches":{},
    }
    seen={}

    def fake_aerosol(_target, rows, *_a, **_k):
        seen["aerosol_max_distance"]=float(rows["distance_km"].max())
        return _zero_tau(),"VIEW_AEROSOL_3D_RESOLVED",5.0,{"required_segment_count":1,"resolved_segment_count":1,"temporal_fallback_segment_count":0,"temporal_missing_segment_count":0,"lowest_endpoint_snap_segment_count":0}

    def fake_gas(_target, rows, *_a, **_k):
        seen["gas_max_distance"]=float(rows["distance_km"].max())
        return _zero_tau(),"VIEW_GAS_RT_RESOLVED",5.0

    def fake_cloud(*_a, **_k):
        sink=_k.get("diagnostic_sink")
        if sink is not None:
            sink.update({"state":"GLOW_OBSERVER_CLOUD_PATH_CLEAR_DIAGNOSTIC","unresolved_blocker_count":0,"conflict_blocker_count":0,"unresolved_layer_ids":"","conflict_states":""})
        return 0.0,0.0,"VIEW_CLOUD_PATH_CLEAR",0,""

    monkeypatch.setattr(vs,"_integrate_view_aerosol",fake_aerosol)
    monkeypatch.setattr(vs,"_integrate_view_gas",fake_gas)
    monkeypatch.setattr(vs,"_cloud_expected_tau",fake_cloud)

    out=vs.build_viewing_spectral_extinction(targets,cloud,optics,aerosol,gas,None,runtime_context=ctx)
    assert not out.empty
    # The target ends at 5 km, but both integrators receive the full 0/5/10 km route group.
    # Each integrator remains responsible for its own target-distance bound, as before.
    assert seen == {"aerosol_max_distance":10.0,"gas_max_distance":10.0}
