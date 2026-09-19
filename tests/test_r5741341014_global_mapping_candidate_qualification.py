import pandas as pd
import firecloud

from firecloud.ice_microphysics_mapping_candidates import (
    SCIENCE_BASELINE, STEP3_MODE,
    build_global_mapping_candidate_registry,
    build_global_mapping_qualification_gate,
    global_mapping_candidate_contract_payload,
)
from firecloud.case_integrity import build_analysis_integrity_audit, build_archive_integrity_audit, PASS, FAIL


def test_release_and_global_first_step3_contract():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.30.10"
    assert SCIENCE_BASELINE == "R5.7.41.2_SHADOW_COT_AB_FROZEN"
    assert STEP3_MODE == "GLOBAL_MAPPING_CANDIDATE_QUALIFICATION_ONLY"


def test_global_registry_prioritizes_current_gfs_without_authorizing_mapping():
    reg = build_global_mapping_candidate_registry().set_index("candidate_id")
    gfs = reg.loc["NOAA_GFS_V16_GFDL_MP_CURRENT"]
    assert bool(gfs["global_coverage"]) is True
    assert bool(gfs["current_operational"]) is True
    assert bool(gfs["runtime_ingested"]) is True
    assert int(gfs["investigation_priority"]) == 1
    assert "EXACT_RUNTIME" in str(gfs["qualification_state"])
    assert bool(gfs["mapping_candidate_eligible"]) is False
    assert bool(gfs["production_eligible"]) is False


def test_future_gfsv17_thompson_is_mass_number_candidate_but_not_current():
    reg = build_global_mapping_candidate_registry().set_index("candidate_id")
    row = reg.loc["NOAA_GFS_V17_THOMPSON_FUTURE"]
    assert bool(row["global_coverage"]) is True
    assert bool(row["current_operational"]) is False
    assert "ICE_NUMBER" in str(row["ice_number_state"])
    assert "MASS_PLUS_NUMBER" in str(row["reconstruction_path"])
    assert bool(row["mapping_candidate_eligible"]) is False


def test_gfdl_mpv3_reference_is_explicit_psd_but_not_substituted_for_gfsv16():
    reg = build_global_mapping_candidate_registry().set_index("candidate_id")
    row = reg.loc["GFDL_SHIELD_MPV3_GLOBAL_REFERENCE"]
    assert "EXPLICIT_GAMMA_PSD" in str(row["psd_scheme_state"])
    assert bool(row["current_operational"]) is False
    assert "NOT_PROVEN_IDENTICAL_TO_GFSV16" in str(row["qualification_blockers"])
    assert bool(row["mapping_candidate_eligible"]) is False


def test_global_gate_stays_fail_closed():
    gate = build_global_mapping_qualification_gate().iloc[0]
    assert bool(gate["global_coverage_preferred"]) is True
    assert bool(gate["GLOBAL_CURRENT_OPERATIONAL_CANDIDATE_IDENTIFIED"]) is True
    assert bool(gate["GLOBAL_FUTURE_MOMENT_CANDIDATE_IDENTIFIED"]) is True
    assert bool(gate["GLOBAL_EXPLICIT_PSD_REFERENCE_IDENTIFIED"]) is True
    assert gate["primary_investigation_target"] == "NOAA_GFS_V16_GFDL_MP_CURRENT"
    assert bool(gate["CURRENT_GLOBAL_DIRECT_DMAX_ELIGIBLE"]) is False
    assert bool(gate["CURRENT_GLOBAL_SCHEME_PSD_RECONSTRUCTION_ELIGIBLE"]) is False
    assert bool(gate["MAPPING_CANDIDATE_ELIGIBLE"]) is False
    assert bool(gate["PRODUCTION_ICE_OPTICS_READY"]) is False
    assert bool(gate["physics_promotion_allowed"]) is False


def test_candidate_contract_blocks_cross_version_and_semantic_shortcuts():
    c = global_mapping_candidate_contract_payload(physicscore_version=firecloud.__version__)
    assert c["contract_version"] == "FIRECLOUD_ICE_GLOBAL_MAPPING_CANDIDATE_V1"
    assert c["global_coverage_preferred"] is True
    assert c["physics_promotion_allowed"] is False
    assert c["primary_investigation_target"] == "NOAA_GFS_V16_GFDL_MP_CURRENT"
    forbidden = set(c["forbidden_shortcuts"])
    for key in (
        "GFDL_MPv3_parameters_assumed_identical_to_GFSv16_without_version_proof",
        "GFSv17_Thompson_assumed_operational_before_implementation",
        "ICON_double_moment_assumed_for_global_operational_grid",
        "effective_radius_or_effective_diameter_treated_as_Dmax",
        "scheme_particle_diameter_treated_as_Yang_Bi_Dmax_without_semantic_validation",
    ):
        assert key in forbidden


def _result():
    return {
        "ice_microphysics_mapping_candidate_required": True,
        "v1_ice_microphysics_global_mapping_candidate_registry": build_global_mapping_candidate_registry(),
        "v1_ice_microphysics_global_mapping_qualification_gate": build_global_mapping_qualification_gate(),
        "ice_microphysics_global_mapping_candidate_contract": global_mapping_candidate_contract_payload(
            physicscore_version=firecloud.__version__
        ),
    }


def test_analysis_integrity_enforces_step3_candidate_evidence():
    audit = build_analysis_integrity_audit(_result()).set_index("check_id")
    for cid in (
        "ICE_MICROPHYSICS_GLOBAL_CANDIDATE_EVIDENCE_PRESENT",
        "ICE_MICROPHYSICS_GLOBAL_CANDIDATE_CONTRACT_FREEZE",
        "ICE_MICROPHYSICS_GLOBAL_CANDIDATE_FAIL_CLOSED",
    ):
        assert audit.loc[cid, "status"] == PASS

    broken = _result()
    broken["ice_microphysics_global_mapping_candidate_contract"] = {}
    audit2 = build_analysis_integrity_audit(broken).set_index("check_id")
    assert audit2.loc["ICE_MICROPHYSICS_GLOBAL_CANDIDATE_EVIDENCE_PRESENT", "status"] == FAIL


def test_case_archive_requires_step3_candidate_members():
    required = [
        "ice_microphysics_global_mapping_candidate_registry.csv",
        "ice_microphysics_global_mapping_qualification_gate.csv",
        "ice_microphysics_global_mapping_candidate_contract.json",
    ]
    manifest = pd.DataFrame({"artifact": required})
    audit = build_archive_integrity_audit(manifest, pd.DataFrame()).set_index("check_id")
    for name in required:
        assert audit.loc[f"ARCHIVE_MEMBER::{name}", "status"] == PASS
