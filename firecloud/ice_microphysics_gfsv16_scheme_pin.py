"""Ice Optics Phase 2 Step 3B — GFS v16 exact-scheme pinning evidence.

R5.7.41.3.4.10.15.1 preserves the Step 3B evidence/qualification-only contract.  It pins the strongest
publicly reproducible GFS v16 GFDL-MP facts without claiming that a public
CCPP emulation source tree is byte-identical to the NCEP production binary.
No Dmax/PSD mapping is executed and no Ice Optics production promotion is
allowed.
"""
from __future__ import annotations
from typing import Any
import pandas as pd

SCIENCE_BASELINE = "R5.7.41.2_SHADOW_COT_AB_FROZEN"
STEP3B_VERSION = "R5.7.41.3.4.10.15.1"
STEP3B_MODE = "GFSV16_EXACT_SCHEME_PINNING_EVIDENCE_ONLY"
PHYSICS_PROMOTION_ALLOWED = False
EVIDENCE_AS_OF = "2026-09-16"

EVIDENCE_COLUMNS = [
    "step3b_version","science_baseline","step3b_mode","evidence_id","evidence_type",
    "pin_status","value","semantic_role","authoritative_for_runtime_mapping",
    "source_reference","source_path","source_sha","notes",
]

_EVIDENCE: tuple[dict[str, Any], ...] = (
    {
        "evidence_id":"GFSV16_OPERATIONAL_MICROPHYSICS_FAMILY",
        "evidence_type":"OPERATIONAL_IMPLEMENTATION",
        "pin_status":"PINNED_FAMILY",
        "value":"GFDL Cloud Microphysics",
        "semantic_role":"CURRENT_OPERATIONAL_GFSV16_MICROPHYSICS_FAMILY",
        "authoritative_for_runtime_mapping":False,
        "source_reference":"https://www.emc.ncep.noaa.gov/emc/pages/numerical_forecast_systems/gfs/documentation.php",
        "source_path":"NOAA EMC GFS documentation / GFS v16 implementation material",
        "source_sha":"",
        "notes":"Operational GFS v16 is documented as using GFDL Cloud Microphysics. Family identity alone is insufficient for Dmax/PSD reconstruction.",
    },
    {
        "evidence_id":"CCPP_GFDL_V1_2019_PUBLIC_REPRODUCTION_PATH",
        "evidence_type":"PUBLIC_SOURCE_TREE",
        "pin_status":"PINNED_PUBLIC_REPRODUCTION",
        "value":"physics/MP/GFDL/v1_2019",
        "semantic_role":"GFSV16_COMPATIBLE_PUBLIC_GFDL_V1_IMPLEMENTATION",
        "authoritative_for_runtime_mapping":False,
        "source_reference":"https://github.com/ufs-community/ccpp-physics/tree/ufs/dev/physics/MP/GFDL/v1_2019",
        "source_path":"physics/MP/GFDL/v1_2019",
        "source_sha":"directory:f92f82addd292b00c634060a9cc398a7d45fe484",
        "notes":"The public CCPP tree separates v1_2019 from v3_2022. This proves MPv3 must not be substituted for the GFS v16-compatible v1 path.",
    },
    {
        "evidence_id":"GFDL_V1_MICROPHYSICS_MODULE",
        "evidence_type":"PUBLIC_SOURCE_FILE",
        "pin_status":"PINNED_PUBLIC_SOURCE_FILE",
        "value":"gfdl_cloud_microphys_mod.F90",
        "semantic_role":"GFDL_V1_CLOUD_MICROPHYSICS_IMPLEMENTATION",
        "authoritative_for_runtime_mapping":False,
        "source_reference":"https://raw.githubusercontent.com/ufs-community/ccpp-physics/ufs/dev/physics/MP/GFDL/v1_2019/gfdl_cloud_microphys_mod.F90",
        "source_path":"physics/MP/GFDL/v1_2019/gfdl_cloud_microphys_mod.F90",
        "source_sha":"ad0304074e17a7b83be2f0fe016345b7f11be4ef",
        "notes":"Public source file contains cloud-ice effective-radius branches and hydrometeor process implementation.",
    },
    {
        "evidence_id":"GFSV16_REIFLAG",
        "evidence_type":"SUITE_NAMELIST",
        "pin_status":"PINNED_EMULATION_NAMELIST",
        "value":"reiflag=2",
        "semantic_role":"ICE_EFFECTIVE_RADIUS_SCHEME_SELECTOR",
        "authoritative_for_runtime_mapping":False,
        "source_reference":"https://dtcenter.ucar.edu/GMTB/v7.0.0/sci_doc/_g_f_s_v16_page.html",
        "source_path":"GFS_v16 suite / gfdl_cloud_microphysics_nml",
        "source_sha":"",
        "notes":"CCPP GFS_v16 suite emulates the operational implementation; reiflag=2 is pinned for the emulation contract, not claimed as a production-binary hash proof.",
    },
    {
        "evidence_id":"GFSV16_REIFLAG2_SEMANTIC",
        "evidence_type":"SOURCE_SEMANTIC",
        "pin_status":"PINNED_EFFECTIVE_RADIUS_SEMANTIC",
        "value":"cloud-ice effective radius branch",
        "semantic_role":"EFFECTIVE_RADIUS_NOT_MAXIMUM_DIMENSION",
        "authoritative_for_runtime_mapping":False,
        "source_reference":"https://raw.githubusercontent.com/ufs-community/ccpp-physics/ufs/dev/physics/MP/GFDL/v1_2019/gfdl_cloud_microphys_mod.F90",
        "source_path":"physics/MP/GFDL/v1_2019/gfdl_cloud_microphys_mod.F90 :: reiflag branch",
        "source_sha":"ad0304074e17a7b83be2f0fe016345b7f11be4ef",
        "notes":"The branch computes rei and bounds it as effective radius. This is not Yang/Bi maximum_dimension_um and cannot be silently relabeled Dmax.",
    },
    {
        "evidence_id":"GFDL_V1_REI_BOUNDS",
        "evidence_type":"SOURCE_PARAMETER",
        "pin_status":"PINNED_PUBLIC_PARAMETER_DEFAULTS",
        "value":"reimin=10.0 um; reimax=150.0 um",
        "semantic_role":"ICE_EFFECTIVE_RADIUS_BOUNDS",
        "authoritative_for_runtime_mapping":False,
        "source_reference":"https://raw.githubusercontent.com/ufs-community/ccpp-physics/ufs/dev/physics/MP/GFDL/module_gfdlmp_param.F90",
        "source_path":"physics/MP/GFDL/module_gfdlmp_param.F90",
        "source_sha":"c20e229466a69f5d5e1705bded8a7b20fbd3977e",
        "notes":"Public defaults constrain rei only. They do not define Yang/Bi Dmax, habit, roughness, or a bulk PSD bridge.",
    },
    {
        "evidence_id":"NCEP_PRODUCTION_BINARY_EXACT_COMMIT",
        "evidence_type":"PRODUCTION_PROVENANCE",
        "pin_status":"UNRESOLVED",
        "value":"NOT_PUBLICLY_PINNED",
        "semantic_role":"EXACT_OPERATIONAL_SOURCE_REVISION",
        "authoritative_for_runtime_mapping":False,
        "source_reference":"",
        "source_path":"",
        "source_sha":"",
        "notes":"Public CCPP documentation explicitly describes its GFS_v16 suite as emulating the operational implementation; no byte-identical production source revision/commit is proven here.",
    },
    {
        "evidence_id":"YANG_BI_DMAX_SEMANTIC_BRIDGE",
        "evidence_type":"OPTICAL_MAPPING_SEMANTIC",
        "pin_status":"UNRESOLVED",
        "value":"NO_VALIDATED_BRIDGE",
        "semantic_role":"EFFECTIVE_RADIUS_TO_MAXIMUM_DIMENSION_BRIDGE",
        "authoritative_for_runtime_mapping":False,
        "source_reference":"",
        "source_path":"",
        "source_sha":"",
        "notes":"A cloud-ice effective radius cannot be converted to Yang/Bi Dmax without a habit/PSD/mass-size compatible mapping and validation.",
    },
)


def build_gfsv16_scheme_pin_evidence() -> pd.DataFrame:
    rows=[]
    for item in _EVIDENCE:
        row={
            "step3b_version":STEP3B_VERSION,
            "science_baseline":SCIENCE_BASELINE,
            "step3b_mode":STEP3B_MODE,
            **item,
        }
        rows.append(row)
    return pd.DataFrame(rows, columns=EVIDENCE_COLUMNS)


def build_gfsv16_scheme_pin_gate(evidence: pd.DataFrame | None = None) -> pd.DataFrame:
    df = evidence if isinstance(evidence,pd.DataFrame) else build_gfsv16_scheme_pin_evidence()
    ids=set(df.get("evidence_id",pd.Series(dtype=str)).astype(str)) if not df.empty else set()
    statuses={str(r.get("evidence_id")):str(r.get("pin_status")) for _,r in df.iterrows()} if not df.empty else {}
    family = statuses.get("GFSV16_OPERATIONAL_MICROPHYSICS_FAMILY") == "PINNED_FAMILY"
    public_v1 = statuses.get("CCPP_GFDL_V1_2019_PUBLIC_REPRODUCTION_PATH") == "PINNED_PUBLIC_REPRODUCTION"
    namelist = statuses.get("GFSV16_REIFLAG") == "PINNED_EMULATION_NAMELIST"
    rei_sem = statuses.get("GFSV16_REIFLAG2_SEMANTIC") == "PINNED_EFFECTIVE_RADIUS_SEMANTIC"
    prod_commit = statuses.get("NCEP_PRODUCTION_BINARY_EXACT_COMMIT") != "UNRESOLVED"
    dmax_bridge = statuses.get("YANG_BI_DMAX_SEMANTIC_BRIDGE") != "UNRESOLVED"
    partial = bool(family and public_v1 and namelist and rei_sem)
    blockers=[]
    if not prod_commit: blockers.append("NCEP_PRODUCTION_BINARY_EXACT_COMMIT_UNRESOLVED")
    if not dmax_bridge: blockers.append("EFFECTIVE_RADIUS_TO_YANG_BI_DMAX_BRIDGE_UNRESOLVED")
    blockers += ["ICE_HABIT_UNRESOLVED","ICE_ROUGHNESS_UNRESOLVED","NO_INDEPENDENT_DMAX_MAPPING_VALIDATION"]
    row={
        "step3b_version":STEP3B_VERSION,
        "science_baseline":SCIENCE_BASELINE,
        "step3b_mode":STEP3B_MODE,
        "GFSV16_GFDL_FAMILY_PINNED":family,
        "GFSV16_PUBLIC_V1_2019_SOURCE_PATH_PINNED":public_v1,
        "GFSV16_EMULATION_NAMELIST_REIFLAG_PINNED":namelist,
        "GFSV16_EFFECTIVE_RADIUS_SEMANTIC_PINNED":rei_sem,
        "GFSV16_PUBLIC_REPRODUCTION_CONTRACT_PARTIALLY_PINNED":partial,
        "NCEP_PRODUCTION_BINARY_EXACT_COMMIT_PINNED":prod_commit,
        "YANG_BI_DMAX_SEMANTIC_BRIDGE_VALIDATED":dmax_bridge,
        "GFSV16_DMAX_MAPPING_ELIGIBLE":False,
        "GFSV16_PSD_RECONSTRUCTION_ELIGIBLE":False,
        "PRODUCTION_ICE_OPTICS_READY":False,
        "physics_promotion_allowed":False,
        "evidence_row_count":int(len(df)),
        "qualification_state":"GFSV16_EFFECTIVE_RADIUS_CONTRACT_PARTIALLY_PINNED_DMAX_BLOCKED" if partial else "GFSV16_SCHEME_PINNING_INCOMPLETE",
        "qualification_blockers":"|".join(blockers),
        "detail":"GFDL v1/2019 public reproduction path + GFSv16 emulation reiflag=2/effective-radius semantic are pinned; production-binary exact commit and Yang/Bi Dmax bridge remain unresolved.",
    }
    return pd.DataFrame([row])


def gfsv16_scheme_pin_contract_payload(*, physicscore_version: str | None=None) -> dict[str,Any]:
    return {
        "contract_version":"FIRECLOUD_ICE_GFSV16_SCHEME_PIN_V1",
        "physicscore_version":physicscore_version or "",
        "step3b_version":STEP3B_VERSION,
        "science_baseline":SCIENCE_BASELINE,
        "mode":STEP3B_MODE,
        "primary_model":"NOAA/NCEP GFS v16",
        "microphysics_family":"GFDL Cloud Microphysics",
        "public_reproduction_path":"physics/MP/GFDL/v1_2019",
        "emulation_namelist_reiflag":2,
        "pinned_size_semantic":"cloud_ice_effective_radius",
        "authoritative_runtime_size_axis":"maximum_dimension_um",
        "effective_radius_is_dmax":False,
        "production_binary_exact_commit_pinned":False,
        "dmax_mapping_eligible":False,
        "psd_reconstruction_eligible":False,
        "production_ice_optics_ready":False,
        "physics_promotion_allowed":False,
        "forbidden_shortcuts":[
            "CCPP_GFSv16_emulation_claimed_byte_identical_to_NCEP_production_binary",
            "GFDL_v1_effective_radius_treated_as_Yang_Bi_Dmax",
            "GFDL_MPv3_PSD_parameters_substituted_for_GFSv16_v1",
            "reiflag2_effective_radius_bounds_used_as_Dmax_bounds",
            "effective_radius_to_Dmax_without_habit_PSD_mass_size_contract",
            "fixed_habit_default",
            "fixed_surface_roughness_default",
        ],
        "promotion_requirements":[
            "exact_operational_source_revision_or_equivalent_authoritative_provenance",
            "scheme_specific_particle_size_semantic_proof",
            "Yang_Bi_Dmax_bridge_with_habit_PSD_mass_size_compatibility",
            "uncertainty_domain_and_fail_close_boundaries",
            "independent_validation",
            "separate_production_promotion_gate",
        ],
        "frozen_science_unchanged":True,
    }
