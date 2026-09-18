import pandas as pd
import firecloud

from firecloud.ice_microphysics_source_registry import (
    SCIENCE_BASELINE,
    STEP2_MODE,
    build_source_capability_registry,
    build_source_eligibility_gate,
    source_registry_contract_payload,
)
from firecloud.case_integrity import build_analysis_integrity_audit, build_archive_integrity_audit, PASS, FAIL


def test_release_and_frozen_step2_mode():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.30.5"
    assert SCIENCE_BASELINE == "R5.7.41.2_SHADOW_COT_AB_FROZEN"
    assert STEP2_MODE == "SOURCE_CAPABILITY_SURVEY_ONLY"


def test_registry_separates_mass_effective_size_moment_and_geographic_scope():
    reg = build_source_capability_registry().set_index("source_id")
    assert reg.loc["NOAA_GFS_0P25", "capability_class"] == "MASS_ONLY"
    assert bool(reg.loc["NOAA_GFS_0P25", "taiwan_operational_coverage"]) is True
    assert reg.loc["DWD_ICON_GLOBAL_OPEN", "capability_class"] == "MASS_ONLY"
    assert "EFFECTIVE_RADIUS_ONLY" in reg.loc["ECMWF_IFS_RADIATION_EFFECTIVE_SIZE_REFERENCE", "capability_class"]
    assert bool(reg.loc["ECMWF_IFS_RADIATION_EFFECTIVE_SIZE_REFERENCE", "mapping_eligible"]) is False
    assert "MASS_PLUS_NUMBER_MOMENT" in reg.loc["NOAA_RAP_NATIVE_REFERENCE", "capability_class"]
    assert bool(reg.loc["NOAA_RAP_NATIVE_REFERENCE", "taiwan_operational_coverage"]) is False
    assert bool(reg["mapping_eligible"].any()) is False
    assert bool(reg["production_eligible"].any()) is False


def test_source_gate_fails_closed_without_taiwan_dmax_or_psd_source():
    gate = build_source_eligibility_gate(build_source_capability_registry()).iloc[0]
    assert bool(gate["TAIWAN_MASS_SOURCE_AVAILABLE"]) is True
    assert bool(gate["TAIWAN_DIRECT_DMAX_SOURCE_AVAILABLE"]) is False
    assert bool(gate["TAIWAN_PSD_SOURCE_AVAILABLE"]) is False
    assert bool(gate["DMAX_SOURCE_SELECTION_ELIGIBLE"]) is False
    assert bool(gate["PSD_SOURCE_SELECTION_ELIGIBLE"]) is False
    assert bool(gate["PRODUCTION_ICE_OPTICS_READY"]) is False
    assert bool(gate["physics_promotion_allowed"]) is False
    assert gate["eligibility_state"] == "NO_AUTHORITATIVE_TAIWAN_SIZE_OR_PSD_SOURCE"


def test_contract_explicitly_blocks_effective_size_and_mass_number_shortcuts():
    c = source_registry_contract_payload(physicscore_version=firecloud.__version__)
    assert c["contract_version"] == "FIRECLOUD_ICE_MICROPHYSICS_SOURCE_REGISTRY_V1"
    assert c["physics_promotion_allowed"] is False
    assert c["authoritative_runtime_size_axis"] == "maximum_dimension_um"
    assert "effective_radius_to_Dmax_without_validated_contract" in c["forbidden_shortcuts"]
    assert "mass_plus_number_to_Dmax_without_scheme_specific_distribution_contract" in c["forbidden_shortcuts"]
    assert "reference_only_source_used_as_Taiwan_operational_source" in c["forbidden_shortcuts"]


def _source_result():
    return {
        "ice_microphysics_source_registry_required": True,
        "v1_ice_microphysics_source_capability_registry": build_source_capability_registry(),
        "v1_ice_microphysics_source_eligibility_gate": build_source_eligibility_gate(),
        "ice_microphysics_source_registry_contract": source_registry_contract_payload(physicscore_version=firecloud.__version__),
    }


def test_analysis_integrity_enforces_all_three_source_registry_gates():
    audit = build_analysis_integrity_audit(_source_result()).set_index("check_id")
    for cid in (
        "ICE_MICROPHYSICS_SOURCE_REGISTRY_EVIDENCE_PRESENT",
        "ICE_MICROPHYSICS_SOURCE_REGISTRY_CONTRACT_FREEZE",
        "ICE_MICROPHYSICS_SOURCE_SELECTION_FAIL_CLOSED",
    ):
        assert audit.loc[cid, "status"] == PASS

    broken = _source_result()
    broken["ice_microphysics_source_registry_contract"] = {}
    audit2 = build_analysis_integrity_audit(broken).set_index("check_id")
    assert audit2.loc["ICE_MICROPHYSICS_SOURCE_REGISTRY_EVIDENCE_PRESENT", "status"] == FAIL


def test_case_archive_requires_source_registry_evidence_members():
    required = [
        "ice_microphysics_source_capability_registry.csv",
        "ice_microphysics_source_eligibility_gate.csv",
        "ice_microphysics_source_registry_contract.json",
    ]
    manifest = pd.DataFrame({"artifact": required})
    audit = build_archive_integrity_audit(manifest, pd.DataFrame()).set_index("check_id")
    for name in required:
        assert audit.loc[f"ARCHIVE_MEMBER::{name}", "status"] == PASS

    manifest2 = pd.DataFrame({"artifact": required[:-1]})
    audit2 = build_archive_integrity_audit(manifest2, pd.DataFrame()).set_index("check_id")
    assert audit2.loc[f"ARCHIVE_MEMBER::{required[-1]}", "status"] == FAIL
