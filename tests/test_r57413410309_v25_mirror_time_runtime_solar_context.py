import json
from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import (
    build_fu96_rrtmg_band_weighting_provenance_evidence,
    build_fu96_rrtmg_band_weighting_provenance_gate,
    fu96_rrtmg_band_weighting_provenance_contract_payload,
)

def test_step3q9_mirror_import_time_is_not_source_time():
    e=build_fu96_rrtmg_band_weighting_provenance_evidence().set_index("check_id")
    assert e.loc["RRTM_SW_V25_EXTERNAL_MIRROR_IMPORT_TIME_SEPARATED_FROM_SOURCE_TIME","status"]=="PASS_QUALIFIED"
    assert "2020" in e.loc["RRTM_SW_V25_EXTERNAL_MIRROR_IMPORT_TIME_SEPARATED_FROM_SOURCE_TIME","observed"]
    assert "2004" in e.loc["RRTM_SW_V25_EXTERNAL_MIRROR_IMPORT_TIME_SEPARATED_FROM_SOURCE_TIME","observed"]

def test_step3q9_official_runtime_solar_context_does_not_unlock_generator():
    e=build_fu96_rrtmg_band_weighting_provenance_evidence()
    g=build_fu96_rrtmg_band_weighting_provenance_gate(e).iloc[0]
    assert bool(g["AER_OFFICIAL_RRTM_SW_V25_RUNTIME_SOLAR_CONTEXT_PINNED"]) is True
    assert bool(g["RRTM_SW_V25_RUNTIME_SOLAR_CONTEXT_EQUALS_FU_CLOUD_TABLE_WEIGHT_VECTOR"]) is False
    assert bool(g["EXACT_FU96_BAND_WEIGHTING_AVAILABLE"]) is False
    assert bool(g["TAU_ICE_PRODUCTION_ALLOWED"]) is False

def test_step3q9_contract_identity():
    p=fu96_rrtmg_band_weighting_provenance_contract_payload()
    assert p["contract_version"]=="FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_18"
    assert p["step_version"]=="R5.7.41.3.4.10.30.18"
    assert p["qualification_state"]=="PASS_FAIL_CLOSED_FU96_PRIMARY_0P700UM_BOUNDARY_AND_BAND24_NONASSOCIATIVE_REAVERAGING_BARRIER_QUALIFIED_EXACT_RRTM_BAND24_25_REALIZATION_UNRECOVERED"
    assert p["sources"]["rrtm_sw_v25_external_import_date_utc"]=="2020-03-17T22:23:17Z"
