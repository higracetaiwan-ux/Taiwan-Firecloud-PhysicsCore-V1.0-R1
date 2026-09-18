import pandas as pd
import firecloud

from firecloud.ice_microphysics_gfsv16_scheme_pin import (
    SCIENCE_BASELINE, STEP3B_MODE,
    build_gfsv16_scheme_pin_evidence,
    build_gfsv16_scheme_pin_gate,
    gfsv16_scheme_pin_contract_payload,
)
from firecloud.case_integrity import build_analysis_integrity_audit, build_archive_integrity_audit, PASS, FAIL


def test_release_and_step3b_mode():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.30.2"
    assert SCIENCE_BASELINE == "R5.7.41.2_SHADOW_COT_AB_FROZEN"
    assert STEP3B_MODE == "GFSV16_EXACT_SCHEME_PINNING_EVIDENCE_ONLY"


def test_public_v1_path_and_effective_radius_semantic_are_pinned_without_dmax():
    ev=build_gfsv16_scheme_pin_evidence().set_index("evidence_id")
    assert ev.loc["CCPP_GFDL_V1_2019_PUBLIC_REPRODUCTION_PATH","value"] == "physics/MP/GFDL/v1_2019"
    assert ev.loc["GFSV16_REIFLAG","value"] == "reiflag=2"
    assert ev.loc["GFSV16_REIFLAG2_SEMANTIC","semantic_role"] == "EFFECTIVE_RADIUS_NOT_MAXIMUM_DIMENSION"
    assert ev.loc["YANG_BI_DMAX_SEMANTIC_BRIDGE","pin_status"] == "UNRESOLVED"


def test_gate_is_partial_pin_but_fail_closed():
    g=build_gfsv16_scheme_pin_gate().iloc[0]
    assert bool(g["GFSV16_GFDL_FAMILY_PINNED"])
    assert bool(g["GFSV16_PUBLIC_V1_2019_SOURCE_PATH_PINNED"])
    assert bool(g["GFSV16_EMULATION_NAMELIST_REIFLAG_PINNED"])
    assert bool(g["GFSV16_EFFECTIVE_RADIUS_SEMANTIC_PINNED"])
    assert bool(g["GFSV16_PUBLIC_REPRODUCTION_CONTRACT_PARTIALLY_PINNED"])
    assert not bool(g["NCEP_PRODUCTION_BINARY_EXACT_COMMIT_PINNED"])
    assert not bool(g["YANG_BI_DMAX_SEMANTIC_BRIDGE_VALIDATED"])
    assert not bool(g["GFSV16_DMAX_MAPPING_ELIGIBLE"])
    assert not bool(g["GFSV16_PSD_RECONSTRUCTION_ELIGIBLE"])
    assert not bool(g["PRODUCTION_ICE_OPTICS_READY"])
    assert not bool(g["physics_promotion_allowed"])


def test_contract_blocks_reff_to_dmax_and_mpv3_substitution():
    c=gfsv16_scheme_pin_contract_payload(physicscore_version=firecloud.__version__)
    assert c["public_reproduction_path"] == "physics/MP/GFDL/v1_2019"
    assert c["emulation_namelist_reiflag"] == 2
    assert c["pinned_size_semantic"] == "cloud_ice_effective_radius"
    assert c["effective_radius_is_dmax"] is False
    assert c["production_binary_exact_commit_pinned"] is False
    f=set(c["forbidden_shortcuts"])
    assert "GFDL_v1_effective_radius_treated_as_Yang_Bi_Dmax" in f
    assert "GFDL_MPv3_PSD_parameters_substituted_for_GFSv16_v1" in f


def _result():
    return {
        "ice_microphysics_gfsv16_scheme_pin_required": True,
        "v1_ice_microphysics_gfsv16_scheme_pin_evidence": build_gfsv16_scheme_pin_evidence(),
        "v1_ice_microphysics_gfsv16_scheme_pin_gate": build_gfsv16_scheme_pin_gate(),
        "ice_microphysics_gfsv16_scheme_pin_contract": gfsv16_scheme_pin_contract_payload(physicscore_version=firecloud.__version__),
    }


def test_analysis_integrity_enforces_step3b():
    a=build_analysis_integrity_audit(_result()).set_index("check_id")
    ids=["ICE_MICROPHYSICS_GFSV16_SCHEME_PIN_EVIDENCE_PRESENT","ICE_MICROPHYSICS_GFSV16_SCHEME_PIN_CONTRACT_FREEZE","ICE_MICROPHYSICS_GFSV16_SCHEME_PIN_FAIL_CLOSED"]
    assert all(a.loc[i,"status"] == PASS for i in ids)
    b=_result(); b["ice_microphysics_gfsv16_scheme_pin_contract"]={}
    a2=build_analysis_integrity_audit(b).set_index("check_id")
    assert a2.loc[ids[0],"status"] == FAIL


def test_archive_requires_step3b_members():
    names=["ice_microphysics_gfsv16_scheme_pin_evidence.csv","ice_microphysics_gfsv16_scheme_pin_gate.csv","ice_microphysics_gfsv16_scheme_pin_contract.json"]
    a=build_archive_integrity_audit(pd.DataFrame({"artifact":names}),pd.DataFrame()).set_index("check_id")
    assert all(a.loc[f"ARCHIVE_MEMBER::{n}","status"] == PASS for n in names)
