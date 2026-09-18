"""Ice Optics Phase 2 Step 3N — Fu96/RRTMG independent bulk-band SSA/g qualification.

This module intentionally qualifies source provenance and spectral semantics only.
RRTMG/GFS stores Fu (1996) ice-cloud ``ssaice3`` and ``asyice3`` coefficients,
but those are broad-band bulk parameterizations.  They are not relabelled as
monochromatic Yang/Bi values at 550/575/600/650/700/750 nm.

Therefore Step 3N remains diagnostic and fail-closed for exact six-band
like-for-like validation and all production use.
"""
from __future__ import annotations

from typing import Any
import pandas as pd

from . import __version__ as PHYSICSCORE_VERSION

SCIENCE_BASELINE = "R5.7.41.2_SHADOW_COT_AB_FROZEN"
STEP3N_VERSION = "R5.7.41.3.4.10.27"
STEP3N_MODE = "FU96_RRTMG_BULK_BAND_SSA_ASYMMETRY_QUALIFICATION_DIAGNOSTIC_FAIL_CLOSED"
EVIDENCE_AS_OF = "2026-09-18"

FU96_PRIMARY_DOI = "https://doi.org/10.1175/1520-0442(1996)009<2058:AAPOTS>2.0.CO;2"
FU2007_ASYMMETRY_DOI = "https://doi.org/10.1175/2007JAS2289.1"
RRTMG_GEOSCHEM_SOURCE = (
    "https://github.com/geoschem/geos-chem/blob/"
    "a4551f9442183bb572b23e9c2d362e2d34420d3a/GeosRad/rrtmg_sw_init.F90"
)
RRTMG_SOURCE_SHA = "0ccf597d6aa3d6ed40ec592560e3ed94b653ef32"

# RRTMG SW band 25: 16000–22650 cm-1 ~= 441.5–625 nm.
# RRTMG SW band 24: 12850–16000 cm-1 ~= 625–778.2 nm.
# These mappings are spectral containment only; the broad-band optical value is
# not a monochromatic value at the listed wavelength.
SIX_BAND_RRTMG_MAP: dict[int, int] = {
    550: 25,
    575: 25,
    600: 25,
    650: 24,
    700: 24,
    750: 24,
}
RRTMG_VISIBLE_BAND_WAVENUMBER_CM1: dict[int, tuple[float, float]] = {
    24: (12850.0, 16000.0),
    25: (16000.0, 22650.0),
}

EVIDENCE_COLUMNS = [
    "step3n_version",
    "science_baseline",
    "step3n_mode",
    "evidence_id",
    "evidence_type",
    "pin_status",
    "value",
    "semantic_role",
    "authoritative_for_runtime_mapping",
    "source_reference",
    "source_path",
    "source_sha",
    "notes",
]


def _row(
    evidence_id: str,
    evidence_type: str,
    pin_status: str,
    value: str,
    semantic_role: str,
    authoritative_for_runtime_mapping: bool,
    source_reference: str,
    source_path: str,
    source_sha: str,
    notes: str,
) -> dict[str, Any]:
    return {
        "step3n_version": STEP3N_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "step3n_mode": STEP3N_MODE,
        "evidence_id": evidence_id,
        "evidence_type": evidence_type,
        "pin_status": pin_status,
        "value": value,
        "semantic_role": semantic_role,
        "authoritative_for_runtime_mapping": bool(authoritative_for_runtime_mapping),
        "source_reference": source_reference,
        "source_path": source_path,
        "source_sha": source_sha,
        "notes": notes,
    }


def build_fu96_rrtmg_ssa_asymmetry_qualification_evidence() -> pd.DataFrame:
    mapping_value = ";".join(f"{w}nm->RRTMG_band{b}" for w, b in SIX_BAND_RRTMG_MAP.items())
    rows = [
        _row(
            "FU96_PRIMARY_SOLAR_SSA_G_PROVENANCE",
            "PRIMARY_LITERATURE_PROVENANCE",
            "PINNED",
            "Fu1996 solar cirrus parameterizes extinction, single-scattering albedo and asymmetry factor",
            "INDEPENDENT_BULK_OPTICAL_FRAMEWORK_PROVENANCE",
            False,
            FU96_PRIMARY_DOI,
            "Fu (1996), J. Climate 9, 2058-2082",
            "",
            "Primary framework provenance only; not a Yang/Bi monochromatic replacement.",
        ),
        _row(
            "RRTMG_FU96_SSAICE3_ASYICE3_PROVENANCE",
            "INDEPENDENT_IMPLEMENTATION_PROVENANCE",
            "PINNED",
            "ICEFLAG=3 uses Fu1996; RRTMG stores ssaice3/asyice3 high-resolution-table averages",
            "INDEPENDENT_BULK_BAND_REFERENCE_IMPLEMENTATION",
            False,
            RRTMG_GEOSCHEM_SOURCE,
            "GeosRad/rrtmg_sw_init.F90::swcldpr",
            RRTMG_SOURCE_SHA,
            "External implementation chain is independent of the bundled Yang/Bi LUT.",
        ),
        _row(
            "RRTMG_VISIBLE_BAND_24_DOMAIN",
            "SPECTRAL_DOMAIN_PIN",
            "PINNED",
            "12850-16000 cm-1 (~625-778.2 nm)",
            "BROAD_BAND_VISIBLE_REFERENCE_DOMAIN",
            False,
            RRTMG_GEOSCHEM_SOURCE,
            "rrtmg_sw_init.F90::wavenum1/wavenum2",
            RRTMG_SOURCE_SHA,
            "Contains 650/700/750 nm; values remain band averaged.",
        ),
        _row(
            "RRTMG_VISIBLE_BAND_25_DOMAIN",
            "SPECTRAL_DOMAIN_PIN",
            "PINNED",
            "16000-22650 cm-1 (~441.5-625 nm)",
            "BROAD_BAND_VISIBLE_REFERENCE_DOMAIN",
            False,
            RRTMG_GEOSCHEM_SOURCE,
            "rrtmg_sw_init.F90::wavenum1/wavenum2",
            RRTMG_SOURCE_SHA,
            "Contains 550/575/600 nm; values remain band averaged.",
        ),
        _row(
            "SIX_BAND_TO_RRTMG_BROAD_BAND_MAPPING",
            "SPECTRAL_SEMANTIC_MAPPING",
            "PASS_MAPPING_EXPLICIT_NOT_MONOCHROMATIC",
            mapping_value,
            "CONTAINMENT_MAPPING_ONLY",
            False,
            RRTMG_GEOSCHEM_SOURCE,
            "RRTMG SW bands 24/25",
            RRTMG_SOURCE_SHA,
            "No interpolation or duplication may convert a broad-band reference into six monochromatic truths.",
        ),
        _row(
            "INDEPENDENT_BULK_BAND_SSA_REFERENCE",
            "REFERENCE_AVAILABILITY_GATE",
            "PASS_REFERENCE_AVAILABLE",
            "ssaice3",
            "INDEPENDENT_BULK_BAND_SSA_REFERENCE_AVAILABLE",
            False,
            f"{FU96_PRIMARY_DOI}|{RRTMG_GEOSCHEM_SOURCE}",
            "RRTMG Fu96 ice-cloud coefficient table",
            RRTMG_SOURCE_SHA,
            "Availability is not a numerical validation pass.",
        ),
        _row(
            "INDEPENDENT_BULK_BAND_ASYMMETRY_REFERENCE",
            "REFERENCE_AVAILABILITY_GATE",
            "PASS_REFERENCE_AVAILABLE",
            "asyice3",
            "INDEPENDENT_BULK_BAND_ASYMMETRY_REFERENCE_AVAILABLE",
            False,
            f"{FU96_PRIMARY_DOI}|{FU2007_ASYMMETRY_DOI}|{RRTMG_GEOSCHEM_SOURCE}",
            "RRTMG Fu96 ice-cloud coefficient table",
            RRTMG_SOURCE_SHA,
            "g remains habit/aspect-ratio sensitive; availability is not a six-band Yang/Bi validation.",
        ),
        _row(
            "EXACT_SIX_BAND_MONOCHROMATIC_REFERENCE",
            "FULL_OPTICS_BLOCKER",
            "BLOCKED_BROAD_BAND_NOT_MONOCHROMATIC",
            "false",
            "SIX_BAND_EXACT_REFERENCE_PENDING",
            False,
            f"{FU96_PRIMARY_DOI}|{RRTMG_GEOSCHEM_SOURCE}",
            "Step 3N scope guard",
            "",
            "RRTMG broad bands cannot be silently relabelled 550/575/600/650/700/750 nm.",
        ),
        _row(
            "INDEPENDENT_SSA_NUMERIC_VALIDATION",
            "FULL_OPTICS_BLOCKER",
            "BLOCKED_NOT_EXECUTED",
            "false",
            "INDEPENDENT_SSA_VALIDATION_PENDING",
            False,
            f"{FU96_PRIMARY_DOI}|{RRTMG_GEOSCHEM_SOURCE}",
            "Step 3N qualification",
            "",
            "Source capability is pinned; reproducible numerical comparison is not promoted by this step.",
        ),
        _row(
            "INDEPENDENT_ASYMMETRY_NUMERIC_VALIDATION",
            "FULL_OPTICS_BLOCKER",
            "BLOCKED_NOT_EXECUTED",
            "false",
            "INDEPENDENT_ASYMMETRY_VALIDATION_PENDING",
            False,
            f"{FU96_PRIMARY_DOI}|{FU2007_ASYMMETRY_DOI}|{RRTMG_GEOSCHEM_SOURCE}",
            "Step 3N qualification",
            "",
            "Source capability is pinned; reproducible numerical comparison is not promoted by this step.",
        ),
        _row(
            "PRODUCTION_PROMOTION_GUARD",
            "PRODUCTION_GUARD",
            "PASS_FAIL_CLOSED",
            "tau_ice=false;production_ice_optics=false;physics_promotion=false",
            "NO_PRODUCTION_PROMOTION",
            False,
            STEP3N_VERSION,
            "Step 3N contract",
            "",
            "Formation/Viewing/Twilight Glow and frozen production science remain unchanged.",
        ),
    ]
    return pd.DataFrame(rows, columns=EVIDENCE_COLUMNS)


GATE_COLUMNS = [
    "step3n_version",
    "science_baseline",
    "step3n_mode",
    "INDEPENDENT_BULK_BAND_SSA_REFERENCE_AVAILABLE",
    "INDEPENDENT_BULK_BAND_ASYMMETRY_REFERENCE_AVAILABLE",
    "BROAD_BAND_MAPPING_SEMANTICS_PASS",
    "INDEPENDENT_SSA_VALIDATION_PASS",
    "INDEPENDENT_ASYMMETRY_VALIDATION_PASS",
    "FULL_SIX_BAND_LIKE_FOR_LIKE_OPTICAL_VALIDATION_PASS",
    "TAU_ICE_PRODUCTION_ALLOWED",
    "PRODUCTION_ICE_OPTICS_READY",
    "physics_promotion_allowed",
    "qualification_state",
    "qualification_blockers",
]


def build_fu96_rrtmg_ssa_asymmetry_qualification_gate(evidence: pd.DataFrame) -> pd.DataFrame:
    status = dict(zip(evidence.get("evidence_id", []), evidence.get("pin_status", [])))
    ssa_ref = status.get("INDEPENDENT_BULK_BAND_SSA_REFERENCE") == "PASS_REFERENCE_AVAILABLE"
    g_ref = status.get("INDEPENDENT_BULK_BAND_ASYMMETRY_REFERENCE") == "PASS_REFERENCE_AVAILABLE"
    mapping = status.get("SIX_BAND_TO_RRTMG_BROAD_BAND_MAPPING") == "PASS_MAPPING_EXPLICIT_NOT_MONOCHROMATIC"
    return pd.DataFrame([{
        "step3n_version": STEP3N_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "step3n_mode": STEP3N_MODE,
        "INDEPENDENT_BULK_BAND_SSA_REFERENCE_AVAILABLE": bool(ssa_ref),
        "INDEPENDENT_BULK_BAND_ASYMMETRY_REFERENCE_AVAILABLE": bool(g_ref),
        "BROAD_BAND_MAPPING_SEMANTICS_PASS": bool(mapping),
        "INDEPENDENT_SSA_VALIDATION_PASS": False,
        "INDEPENDENT_ASYMMETRY_VALIDATION_PASS": False,
        "FULL_SIX_BAND_LIKE_FOR_LIKE_OPTICAL_VALIDATION_PASS": False,
        "TAU_ICE_PRODUCTION_ALLOWED": False,
        "PRODUCTION_ICE_OPTICS_READY": False,
        "physics_promotion_allowed": False,
        "qualification_state": "INDEPENDENT_BULK_BAND_SSA_G_REFERENCE_PINNED_EXACT_SIX_BAND_VALIDATION_BLOCKED",
        "qualification_blockers": "RRTMG_REFERENCE_IS_BROAD_BAND_NOT_MONOCHROMATIC|INDEPENDENT_SSA_NUMERIC_VALIDATION_PENDING|INDEPENDENT_ASYMMETRY_NUMERIC_VALIDATION_PENDING|EXACT_SIX_BAND_LIKE_FOR_LIKE_REFERENCE_PENDING",
    }], columns=GATE_COLUMNS)


def fu96_rrtmg_ssa_asymmetry_qualification_contract_payload(
    *, physicscore_version: str = PHYSICSCORE_VERSION,
) -> dict[str, Any]:
    evidence = build_fu96_rrtmg_ssa_asymmetry_qualification_evidence()
    gate = build_fu96_rrtmg_ssa_asymmetry_qualification_gate(evidence).iloc[0].to_dict()
    return {
        "contract_version": "FIRECLOUD_ICE_FU96_RRTMG_SSA_ASYMMETRY_QUALIFICATION_V1",
        "physicscore_version": str(physicscore_version),
        "step3n_version": STEP3N_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "mode": STEP3N_MODE,
        "evidence_as_of": EVIDENCE_AS_OF,
        "primary_reference": FU96_PRIMARY_DOI,
        "independent_reference_implementation": RRTMG_GEOSCHEM_SOURCE,
        "independent_reference_source_sha": RRTMG_SOURCE_SHA,
        "rrtmg_visible_band_wavenumber_cm1": {
            str(k): [float(v[0]), float(v[1])] for k, v in RRTMG_VISIBLE_BAND_WAVENUMBER_CM1.items()
        },
        "six_band_rrtmg_broad_band_map": {str(k): int(v) for k, v in SIX_BAND_RRTMG_MAP.items()},
        "broad_band_values_must_not_be_relabelled_monochromatic": True,
        "independent_bulk_band_ssa_reference_available": bool(gate["INDEPENDENT_BULK_BAND_SSA_REFERENCE_AVAILABLE"]),
        "independent_bulk_band_asymmetry_reference_available": bool(gate["INDEPENDENT_BULK_BAND_ASYMMETRY_REFERENCE_AVAILABLE"]),
        "independent_ssa_validation_pass": False,
        "independent_asymmetry_validation_pass": False,
        "full_six_band_like_for_like_optical_validation_pass": False,
        "tau_ice_production_allowed": False,
        "production_ice_optics_ready": False,
        "physics_promotion_allowed": False,
        "formation_viewing_twilight_glow_frozen": True,
        "runtime_habit_inference_allowed": False,
        "runtime_roughness_inference_allowed": False,
        "qualification_state": gate["qualification_state"],
        "qualification_blockers": gate["qualification_blockers"],
    }
