from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import (
    AER_RRTM_RRTMG_FU96_CONTINUITY_ARRAY_COUNT,
    AER_RRTM_RRTMG_FU96_CONTINUITY_VALUE_COUNT,
    build_fu96_rrtmg_band_weighting_provenance_evidence,
    build_fu96_rrtmg_band_weighting_provenance_gate,
    fu96_rrtmg_band_weighting_provenance_contract_payload,
)
from tools.verify_aer_rrtm_rrtmg_fu96_final_table_continuity import compare_tables

EXPECTED_STATE = "PASS_FAIL_CLOSED_FU96_PRIMARY_BAND_FORWARD_RECONSTRUCTION_INPUTS_QUALIFIED_RRTMG_FINE_GRID_AND_EXACT_BAND24_25_REALIZATION_UNRECOVERED"


def test_step3q15_official_aer_cross_generation_continuity_is_qualified():
    e = build_fu96_rrtmg_band_weighting_provenance_evidence().set_index("check_id")
    assert e.loc["AER_RRTMG_SW_2007_FU96_FINAL_TABLE_HISTORY_PINNED", "status"] == "PASS_PINNED"
    assert e.loc["AER_RRTM_SW_2004_TO_RRTMG_SW_2007_FU96_FINAL_TABLE_VALUE_CONTINUITY", "status"] == "PASS_QUALIFIED"
    assert "56 of 56" in e.loc["AER_RRTM_SW_2004_TO_RRTMG_SW_2007_FU96_FINAL_TABLE_VALUE_CONTINUITY", "observed"]
    assert "2576 of 2576" in e.loc["AER_RRTM_SW_2004_TO_RRTMG_SW_2007_FU96_FINAL_TABLE_VALUE_CONTINUITY", "observed"]
    assert e.loc["AER_RRTM_RRTMG_FU96_FINAL_TABLE_CONTINUITY_IS_PREAVERAGING_GENERATOR_RECOVERY", "status"] == "PASS_FORBIDDEN"


def test_step3q15_gate_and_contract_remain_fail_closed():
    g = build_fu96_rrtmg_band_weighting_provenance_gate().iloc[0]
    assert g["qualification_state"] == EXPECTED_STATE
    assert bool(g["AER_RRTMG_SW_2007_FU96_FINAL_TABLE_HISTORY_PINNED"]) is True
    assert bool(g["AER_RRTM_SW_TO_RRTMG_SW_FU96_FINAL_TABLE_CONTINUITY_56_OF_56_ARRAYS_2576_OF_2576_VALUES_QUALIFIED"]) is True
    assert bool(g["AER_RRTM_RRTMG_FU96_FINAL_TABLE_CONTINUITY_IS_PREAVERAGING_GENERATOR_RECOVERY"]) is False
    assert bool(g["RRTM_SW_PREAVERAGING_GENERATOR_RECOVERED"]) is False
    assert bool(g["EXACT_FU96_BAND_WEIGHTING_AVAILABLE"]) is False
    assert bool(g["PRODUCTION_ICE_OPTICS_READY"]) is False
    p = fu96_rrtmg_band_weighting_provenance_contract_payload()
    assert p["contract_version"] == "FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_20"
    assert p["step_version"] == "R5.7.41.3.4.10.30.20"
    q = p["qualified_weighting_semantic_class"]
    assert q["aer_rrtm_rrtmg_fu96_continuity_array_count"] == AER_RRTM_RRTMG_FU96_CONTINUITY_ARRAY_COUNT == 56
    assert q["aer_rrtm_rrtmg_fu96_continuity_value_count"] == AER_RRTM_RRTMG_FU96_CONTINUITY_VALUE_COUNT == 2576
    assert q["aer_rrtm_rrtmg_fu96_final_table_continuity_is_preaveraging_generator_recovery"] is False


def test_step3q15_verifier_requires_all_56_arrays_and_keeps_generator_closed():
    # Minimal synthetic tables covering all required arrays and bands.
    old=[]; new=[]
    for name in ("EXTICE3", "SSAICE3", "ASYICE3", "FDLICE3"):
        for band in range(16,30):
            vals=",".join(f"{(band*100+i)/1e6:.6e}" for i in range(46))
            old.append(f"DATA ({name}(I,{band}),I=1,46) /\n&{vals}/")
            vals2=",".join(f"{(band*100+i)/1e6:.6e}_jprb" for i in range(46))
            new.append(f"{name}(:, {band}) = (/ &\n& {vals2} /)")
    r=compare_tables("\n".join(old), "\n".join(new))
    assert r["array_count"] == 56
    assert r["matched_array_count"] == 56
    assert r["value_count"] == 2576
    assert r["matched_value_count"] == 2576
    assert r["continuity_qualified"] is True
    assert r["preaveraging_generator_recovered"] is False
    assert r["exact_historical_weighting_recovered"] is False
