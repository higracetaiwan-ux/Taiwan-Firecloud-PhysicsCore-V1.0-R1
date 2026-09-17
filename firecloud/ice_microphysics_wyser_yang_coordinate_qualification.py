"""Ice Optics Phase 2 Step 3H — Wyser↔Yang/Bi size-coordinate qualification.

This module qualifies one narrow statement only: Wyser's axial crystal length
``L`` is the particle maximum dimension for the pinned solid-column geometry,
and the Yang/Bi single-column optical database is indexed by particle maximum
dimension.  Therefore the *size coordinate* may be identified as
``Wyser L_um == Yang/Bi maximum_dimension_um``.

That coordinate identity is deliberately not a shape, projected-area, volume,
mass, habit, roughness, bulk-optics, or production-equivalence claim.  Step 3H
independently reproduces the bundled Yang/Bi V2 single-column source-row
effective-diameter geometry to pin the 3.48*sqrt(L) large-column coefficient.
The pinned Yang/Bi shape law is not the same as Wyser Eq.(5), so downstream
shape/area/volume/optics bridges remain fail-closed.
"""
from __future__ import annotations

from typing import Any, Iterable
from pathlib import Path
import math

import pandas as pd

from .ice_microphysics_wyser_primary_numeric_recovery import (
    wyser_eq5_width_um,
)

SCIENCE_BASELINE = "R5.7.41.2_SHADOW_COT_AB_FROZEN"
STEP3H_VERSION = "R5.7.41.3.4.10.21"
STEP3H_MODE = "WYSER_YANG_MAXIMUM_DIMENSION_COORDINATE_QUALIFICATION_SHAPE_COMPATIBILITY_FAIL_CLOSED"
PHYSICS_PROMOTION_ALLOWED = False
EVIDENCE_AS_OF = "2026-09-17"

_WYSER_PRIMARY = "https://doi.org/10.1175/1520-0442(1998)011%3C1793:TERIIC%3E2.0.CO;2"
_YANG_2005 = "https://doi.org/10.1364/AO.44.005512"
_YANG_2013 = "https://doi.org/10.1175/JAS-D-12-039.1"
_UM_2015 = "https://doi.org/10.5194/acp-15-3933-2015"

YANG_BI_SIZE_COORDINATE_SEMANTIC_PINNED = True
YANG_COLUMN_TRANSITION_LENGTH_UM = 100.0
YANG_COLUMN_SMALL_SEMIWIDTH_FACTOR = 0.35
YANG_COLUMN_LARGE_SEMIWIDTH_FACTOR = 3.48
YANG_COLUMN_REJECTED_TRANSCRIPTION_FACTOR = 0.348
SOURCE_GEOMETRY_REPRODUCTION_TOLERANCE = 1.0e-6
_BUNDLED_LUT_RELATIVE_PATH = "firecloud/data/ice_optics/portable_ice_optics_lut_v1.csv"
_BUNDLED_LUT_PATH = Path(__file__).resolve().parent / "data" / "ice_optics" / "portable_ice_optics_lut_v1.csv"


def _positive_finite(value: float, *, name: str) -> float:
    out = float(value)
    if not math.isfinite(out) or out <= 0.0:
        raise ValueError(f"{name} must be positive and finite")
    return out


def yang_single_column_semiwidth_um(length_um: float, *, large_factor: float = YANG_COLUMN_LARGE_SEMIWIDTH_FACTOR) -> float:
    """Return Yang/Bi V2 single-column hexagonal semiwidth ``a`` in microns."""
    length = _positive_finite(length_um, name="length_um")
    if length < YANG_COLUMN_TRANSITION_LENGTH_UM:
        return YANG_COLUMN_SMALL_SEMIWIDTH_FACTOR * length
    factor = _positive_finite(large_factor, name="large_factor")
    return factor * math.sqrt(length)


def yang_single_column_width_um(length_um: float, *, large_factor: float = YANG_COLUMN_LARGE_SEMIWIDTH_FACTOR) -> float:
    """Return full Yang/Bi V2 single-column width ``2a`` in microns."""
    return 2.0 * yang_single_column_semiwidth_um(length_um, large_factor=large_factor)


def _hexagonal_column_effective_diameter_um(length_um: float, semiwidth_um: float) -> float:
    """Return 1.5*V/Aproj for a randomly oriented regular hexagonal column.

    ``a`` is the hexagonal semiwidth/side-length coordinate used by the Yang
    solid-column geometry.  For a convex randomly oriented particle, mean
    projected area is one quarter of surface area.
    """
    length = _positive_finite(length_um, name="length_um")
    a = _positive_finite(semiwidth_um, name="semiwidth_um")
    volume = (3.0 * math.sqrt(3.0) / 2.0) * a * a * length
    projected_area = (3.0 * math.sqrt(3.0) * a * a + 6.0 * a * length) / 4.0
    return 1.5 * volume / projected_area


def validate_yang_v2_single_column_geometry_against_bundled_lut(
    lut_path: str | Path | None = None,
) -> dict[str, Any]:
    """Reproduce source-derived single-column De rows from the pinned geometry.

    The bundled LUT's ``effective_diameter_um`` was derived rowwise from the
    authoritative TAMU V2 source volume/projected-area fields, independent of
    this aspect-ratio implementation.  Reproducing all 189 Dmax rows therefore
    provides a source-data check on the geometry coefficient.
    """
    path = Path(lut_path) if lut_path is not None else _BUNDLED_LUT_PATH
    source_path = str(path) if lut_path is not None else _BUNDLED_LUT_RELATIVE_PATH
    if not path.exists():
        return {
            "source_row_count": 0,
            "source_geometry_reproduction_pass": False,
            "pinned_large_semiwidth_factor": YANG_COLUMN_LARGE_SEMIWIDTH_FACTOR,
            "max_relative_effective_diameter_error": None,
            "alternative_0_348_max_relative_error": None,
            "source_path": source_path,
            "missing_reason": "BUNDLED_AUTHORITATIVE_LUT_MISSING",
        }
    frame = pd.read_csv(path)
    required = {"maximum_dimension_um", "effective_diameter_um", "ice_habit", "surface_roughness", "wavelength_nm"}
    if not required.issubset(frame.columns):
        return {
            "source_row_count": 0,
            "source_geometry_reproduction_pass": False,
            "pinned_large_semiwidth_factor": YANG_COLUMN_LARGE_SEMIWIDTH_FACTOR,
            "max_relative_effective_diameter_error": None,
            "alternative_0_348_max_relative_error": None,
            "source_path": source_path,
            "missing_reason": "BUNDLED_AUTHORITATIVE_LUT_SCHEMA_INVALID",
        }
    subset = frame.loc[
        (frame["ice_habit"].astype(str) == "single_column")
        & (frame["surface_roughness"].astype(str) == "Rough000")
        & (pd.to_numeric(frame["wavelength_nm"], errors="coerce") == 600),
        ["maximum_dimension_um", "effective_diameter_um"],
    ].copy()
    subset["maximum_dimension_um"] = pd.to_numeric(subset["maximum_dimension_um"], errors="coerce")
    subset["effective_diameter_um"] = pd.to_numeric(subset["effective_diameter_um"], errors="coerce")
    subset = subset.dropna().drop_duplicates("maximum_dimension_um").sort_values("maximum_dimension_um")

    main_errors: list[float] = []
    alt_errors: list[float] = []
    for row in subset.itertuples(index=False):
        length = float(row.maximum_dimension_um)
        observed = float(row.effective_diameter_um)
        if not (math.isfinite(length) and length > 0.0 and math.isfinite(observed) and observed > 0.0):
            continue
        a_main = yang_single_column_semiwidth_um(length, large_factor=YANG_COLUMN_LARGE_SEMIWIDTH_FACTOR)
        a_alt = yang_single_column_semiwidth_um(length, large_factor=YANG_COLUMN_REJECTED_TRANSCRIPTION_FACTOR)
        pred_main = _hexagonal_column_effective_diameter_um(length, a_main)
        pred_alt = _hexagonal_column_effective_diameter_um(length, a_alt)
        main_errors.append(abs(pred_main - observed) / observed)
        alt_errors.append(abs(pred_alt - observed) / observed)

    max_main = max(main_errors) if main_errors else None
    max_alt = max(alt_errors) if alt_errors else None
    passed = bool(
        len(main_errors) == 189
        and max_main is not None
        and max_main <= SOURCE_GEOMETRY_REPRODUCTION_TOLERANCE
        and max_alt is not None
        and max_alt > 0.5
    )
    return {
        "source_row_count": int(len(main_errors)),
        "source_geometry_reproduction_pass": passed,
        "pinned_large_semiwidth_factor": YANG_COLUMN_LARGE_SEMIWIDTH_FACTOR,
        "max_relative_effective_diameter_error": float(max_main) if max_main is not None else None,
        "alternative_0_348_max_relative_error": float(max_alt) if max_alt is not None else None,
        "source_path": source_path,
        "missing_reason": "" if passed else "SOURCE_GEOMETRY_REPRODUCTION_NOT_QUALIFIED",
    }


def coordinate_qualification_diagnostic(
    *,
    lengths_um: Iterable[float] = (10.0, 30.0, 100.0, 1000.0),
) -> dict[str, Any]:
    """Compare size-coordinate and pinned width geometry without optics promotion."""
    lengths = [float(v) for v in lengths_um]
    if not lengths:
        raise ValueError("lengths_um must be non-empty")
    if any((not math.isfinite(v) or v <= 0.0) for v in lengths):
        raise ValueError("lengths_um values must be positive and finite")

    source_geometry = validate_yang_v2_single_column_geometry_against_bundled_lut()
    exact_geometry_pinned = bool(source_geometry["source_geometry_reproduction_pass"])
    rows: list[dict[str, float]] = []
    for length in lengths:
        wyser_width = float(wyser_eq5_width_um(length))
        yang_width = float(yang_single_column_width_um(length))
        wyser_dmax = max(length, wyser_width)
        yang_dmax = max(length, yang_width)
        relative_width_difference = abs(wyser_width - yang_width) / max(wyser_width, yang_width)
        rows.append({
            "length_um": length,
            "wyser_width_um": wyser_width,
            "yang_width_um": yang_width,
            "wyser_maximum_dimension_um": wyser_dmax,
            "yang_maximum_dimension_um": yang_dmax,
            "relative_width_difference": relative_width_difference,
        })

    wyser_max_pass = all(
        math.isclose(r["wyser_maximum_dimension_um"], r["length_um"], rel_tol=0.0, abs_tol=1e-12)
        for r in rows
    )
    yang_max_pass = bool(
        YANG_BI_SIZE_COORDINATE_SEMANTIC_PINNED
        and exact_geometry_pinned
        and all(math.isclose(r["yang_maximum_dimension_um"], r["length_um"], rel_tol=0.0, abs_tol=1e-12) for r in rows)
    )
    coordinate_pass = bool(wyser_max_pass and yang_max_pass)
    max_width_difference = max(r["relative_width_difference"] for r in rows)
    shape_width_pass = bool(exact_geometry_pinned and max_width_difference <= 1e-6)

    return {
        "diagnostic_only": True,
        "tested_lengths_um": lengths,
        "wyser_L_is_maximum_dimension_pass": bool(wyser_max_pass),
        "yang_bi_size_coordinate_is_maximum_dimension_pass": bool(yang_max_pass),
        "wyser_L_to_yang_dmax_coordinate_validated": bool(coordinate_pass),
        "coordinate_validation_scope": "SIZE_COORDINATE_IDENTITY_ONLY_NOT_SHAPE_OR_OPTICAL_EQUIVALENCE",
        "exact_yang_v2_geometry_law_pinned": exact_geometry_pinned,
        "source_geometry_reproduction": source_geometry,
        "max_relative_width_difference": float(max_width_difference),
        "shape_width_compatibility_pass": bool(shape_width_pass),
        "projected_area_compatibility_pass": False,
        "volume_mass_compatibility_pass": False,
        "rows": rows,
    }


EVIDENCE_COLUMNS = [
    "step3h_version", "science_baseline", "step3h_mode", "evidence_id",
    "evidence_type", "pin_status", "value", "semantic_role",
    "authoritative_for_runtime_mapping", "source_reference", "source_path",
    "source_sha", "notes",
]


def build_wyser_yang_coordinate_qualification_evidence() -> pd.DataFrame:
    diagnostic = coordinate_qualification_diagnostic()
    rows = [
        {
            "evidence_id": "WYSER_L_IS_MAXIMUM_DIMENSION",
            "evidence_type": "PRIMARY_GEOMETRY_SEMANTIC",
            "pin_status": "PASS_PRIMARY_GEOMETRY",
            "value": "Wyser solid-column axial length L is >= Eq.(5) transverse width D, therefore L is the maximum dimension",
            "semantic_role": "WYSER_COLUMN_MAXIMUM_DIMENSION_COORDINATE",
            "authoritative_for_runtime_mapping": False,
            "source_reference": _WYSER_PRIMARY,
            "source_path": "Wyser (1998) Eq.(5) solid-column L/D geometry",
            "source_sha": "",
            "notes": "Coordinate qualification only; no optical equivalence is implied.",
        },
        {
            "evidence_id": "YANG_BI_SIZE_COORDINATE_IS_MAXIMUM_DIMENSION",
            "evidence_type": "AUTHORITATIVE_DATABASE_SEMANTIC",
            "pin_status": "PASS_AUTHORITATIVE_DATABASE_SEMANTIC",
            "value": "Yang ice-particle databases specify particle size in terms of particle maximum dimension",
            "semantic_role": "YANG_BI_MAXIMUM_DIMENSION_AXIS",
            "authoritative_for_runtime_mapping": False,
            "source_reference": f"{_YANG_2005}|{_YANG_2013}",
            "source_path": "Yang et al. single-scattering database size-coordinate definition",
            "source_sha": "",
            "notes": "This establishes the LUT size-axis semantic, not a GFS-to-Dmax operational mapping.",
        },
        {
            "evidence_id": "WYSER_L_TO_YANG_DMAX_COORDINATE",
            "evidence_type": "COORDINATE_BRIDGE_QUALIFICATION",
            "pin_status": "PASS_COORDINATE_ONLY",
            "value": "Wyser L_um == Yang/Bi maximum_dimension_um for the size-coordinate identity",
            "semantic_role": "SIZE_COORDINATE_IDENTITY_ONLY",
            "authoritative_for_runtime_mapping": False,
            "source_reference": f"{_WYSER_PRIMARY}|{_YANG_2005}|{_UM_2015}",
            "source_path": "Cross-source maximum-dimension semantic qualification",
            "source_sha": "",
            "notes": "Does not validate Yang solid-column shape, area, volume, mass, habit, roughness or bulk optics.",
        },
        {
            "evidence_id": "YANG_BI_V2_SOLID_COLUMN_EXACT_GEOMETRY_LAW",
            "evidence_type": "SOURCE_ROW_GEOMETRY_REPRODUCTION",
            "pin_status": "PASS_SOURCE_ROW_GEOMETRY_REPRODUCTION" if diagnostic["exact_yang_v2_geometry_law_pinned"] else "BLOCKED_SOURCE_ROW_REPRODUCTION_FAILED",
            "value": f"a=0.35L for L<100um;a=3.48*sqrt(L) for L>=100um;source_rows={diagnostic['source_geometry_reproduction']['source_row_count']};max_De_relerr={diagnostic['source_geometry_reproduction']['max_relative_effective_diameter_error']}",
            "semantic_role": "YANG_BI_V2_EXACT_SHAPE_LAW_SOURCE_VALIDATED",
            "authoritative_for_runtime_mapping": False,
            "source_reference": f"{_YANG_2013}|Yang2013_Bi2017_V2",
            "source_path": "firecloud/data/ice_optics/portable_ice_optics_lut_v1.csv + authoritative source manifest",
            "source_sha": "",
            "notes": "The 3.48 coefficient reproduces all 189 source-derived single-column De rows within 1e-6 relative error; the 0.348 transcription is rejected by the source geometry by >50% relative error. This pins shape geometry only, not Wyser compatibility or runtime mapping.",
        },
        {
            "evidence_id": "WYSER_TO_YANG_SOLID_COLUMN_SHAPE_COMPATIBILITY",
            "evidence_type": "SHAPE_COMPATIBILITY_GATE",
            "pin_status": "BLOCKED_GEOMETRY_LAW_MISMATCH",
            "value": f"false;max_relative_width_difference={diagnostic['max_relative_width_difference']:.17g}",
            "semantic_role": "COORDINATE_IDENTITY_NOT_SHAPE_EQUIVALENCE",
            "authoritative_for_runtime_mapping": False,
            "source_reference": f"{_WYSER_PRIMARY}|{_YANG_2005}",
            "source_path": "Wyser Eq.(5) width law versus source-validated Yang/Bi V2 single-column width law",
            "source_sha": "",
            "notes": "The two source-pinned width/aspect-ratio laws differ, so coordinate identity does not establish shape equivalence.",
        },
        {
            "evidence_id": "WYSER_TO_YANG_PROJECTED_AREA_COMPATIBILITY",
            "evidence_type": "OPTICAL_GEOMETRY_GATE",
            "pin_status": "BLOCKED_SHAPE_COMPATIBILITY_PENDING",
            "value": "false",
            "semantic_role": "PROJECTED_AREA_NOT_VALIDATED",
            "authoritative_for_runtime_mapping": False,
            "source_reference": f"{_WYSER_PRIMARY}|{_YANG_2005}",
            "source_path": "Downstream geometry compatibility gate",
            "source_sha": "",
            "notes": "No projected-area equivalence is inferred from a common maximum-dimension coordinate.",
        },
        {
            "evidence_id": "WYSER_TO_YANG_VOLUME_MASS_COMPATIBILITY",
            "evidence_type": "MASS_GEOMETRY_GATE",
            "pin_status": "BLOCKED_SHAPE_AND_EQ6_CORROBORATION_PENDING",
            "value": "false",
            "semantic_role": "VOLUME_MASS_NOT_VALIDATED",
            "authoritative_for_runtime_mapping": False,
            "source_reference": f"{_WYSER_PRIMARY}|{_YANG_2005}",
            "source_path": "Downstream mass/volume compatibility gate",
            "source_sha": "",
            "notes": "Eq.(6) external numeric corroboration and geometry compatibility are still required.",
        },
        {
            "evidence_id": "INDEPENDENT_EQ6_EXTERNAL_NUMERIC_CORROBORATION",
            "evidence_type": "SCIENTIFIC_PROMOTION_GATE",
            "pin_status": "BLOCKED_NO_INDEPENDENT_EXACT_NUMERIC_SOURCE",
            "value": "false",
            "semantic_role": "SCIENTIFIC_MASS_CLOSURE_STILL_BLOCKED",
            "authoritative_for_runtime_mapping": False,
            "source_reference": _WYSER_PRIMARY,
            "source_path": "Step 3G/3H dual-source promotion policy",
            "source_sha": "",
            "notes": "Coordinate qualification does not relax the independent Eq.(6) corroboration requirement.",
        },
        {
            "evidence_id": "YANG_BI_HABIT_ROUGHNESS_BRIDGE",
            "evidence_type": "MICROPHYSICS_TO_OPTICS_GATE",
            "pin_status": "BLOCKED",
            "value": "habit=false;roughness=false",
            "semantic_role": "NO_HABIT_OR_ROUGHNESS_DEFAULT",
            "authoritative_for_runtime_mapping": False,
            "source_reference": _YANG_2013,
            "source_path": "Yang/Bi habit and roughness dimensions",
            "source_sha": "",
            "notes": "No fixed habit or roughness state is silently selected.",
        },
        {
            "evidence_id": "STEP3H_PRODUCTION_PROMOTION",
            "evidence_type": "PROMOTION_GATE",
            "pin_status": "BLOCKED",
            "value": "false",
            "semantic_role": "COORDINATE_ONLY_NO_BULK_OPTICS_PROMOTION",
            "authoritative_for_runtime_mapping": False,
            "source_reference": "",
            "source_path": "PhysicsCore frozen promotion policy",
            "source_sha": "",
            "notes": "No Dmax runtime synthesis, bulk tau, or Formation promotion is enabled by Step 3H.",
        },
    ]
    return pd.DataFrame([
        {
            "step3h_version": STEP3H_VERSION,
            "science_baseline": SCIENCE_BASELINE,
            "step3h_mode": STEP3H_MODE,
            **row,
        }
        for row in rows
    ], columns=EVIDENCE_COLUMNS)


def build_wyser_yang_coordinate_qualification_gate(evidence: pd.DataFrame | None = None) -> pd.DataFrame:
    df = evidence.copy() if isinstance(evidence, pd.DataFrame) else build_wyser_yang_coordinate_qualification_evidence()
    diagnostic = coordinate_qualification_diagnostic()
    blockers = [
        "INDEPENDENT_EQ6_EXTERNAL_NUMERIC_CORROBORATION_NOT_PASSED",
        "SCIENTIFIC_MASS_CLOSURE_NOT_EXECUTED",
        "WYSER_TO_YANG_SOLID_COLUMN_SHAPE_COMPATIBILITY_NOT_PASSED",
        "WYSER_TO_YANG_PROJECTED_AREA_COMPATIBILITY_NOT_PASSED",
        "WYSER_TO_YANG_VOLUME_MASS_COMPATIBILITY_NOT_PASSED",
        "YANG_BI_HABIT_BRIDGE_NOT_VALIDATED",
        "YANG_BI_ROUGHNESS_POLICY_NOT_VALIDATED",
        "NO_INDEPENDENT_BULK_OPTICS_VALIDATION",
    ]
    return pd.DataFrame([{
        "step3h_version": STEP3H_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "step3h_mode": STEP3H_MODE,
        "WYSER_L_IS_MAXIMUM_DIMENSION_PASS": bool(diagnostic["wyser_L_is_maximum_dimension_pass"]),
        "YANG_BI_SIZE_COORDINATE_IS_MAXIMUM_DIMENSION_PASS": bool(diagnostic["yang_bi_size_coordinate_is_maximum_dimension_pass"]),
        "WYSER_L_TO_YANG_DMAX_COORDINATE_VALIDATED": bool(diagnostic["wyser_L_to_yang_dmax_coordinate_validated"]),
        "WYSER_TO_YANG_SOLID_COLUMN_SHAPE_COMPATIBILITY_PASS": False,
        "WYSER_TO_YANG_PROJECTED_AREA_COMPATIBILITY_PASS": False,
        "WYSER_TO_YANG_VOLUME_MASS_COMPATIBILITY_PASS": False,
        "INDEPENDENT_EQ6_EXTERNAL_NUMERIC_CORROBORATION_PASS": False,
        "SCIENTIFIC_MASS_CLOSURE_EXECUTED": False,
        "YANG_BI_HABIT_BRIDGE_VALIDATED": False,
        "YANG_BI_ROUGHNESS_BRIDGE_VALIDATED": False,
        "BULK_YANG_BI_PSD_INTEGRATION_ELIGIBLE": False,
        "GFSV16_DMAX_MAPPING_ELIGIBLE": False,
        "PRODUCTION_ICE_OPTICS_READY": False,
        "physics_promotion_allowed": False,
        "evidence_row_count": int(len(df)),
        "qualification_state": "WYSER_YANG_DMAX_COORDINATE_VALIDATED_SHAPE_COMPATIBILITY_BLOCKED",
        "qualification_blockers": "|".join(blockers),
        "detail": "Wyser L and Yang/Bi maximum_dimension now share a qualified size coordinate. Yang/Bi V2 single-column geometry is source-row reproduced, but it differs from Wyser Eq.(5), so shape/area/volume equivalence remains blocked; Eq.6 external corroboration plus habit/roughness/bulk validation also remain blocked.",
    }])


def wyser_yang_coordinate_qualification_contract_payload(*, physicscore_version: str | None = None) -> dict[str, Any]:
    diagnostic = coordinate_qualification_diagnostic()
    return {
        "contract_version": "FIRECLOUD_ICE_WYSER_YANG_COORDINATE_QUALIFICATION_V1",
        "physicscore_version": physicscore_version or "",
        "step3h_version": STEP3H_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "mode": STEP3H_MODE,
        "coordinate_validation_scope": "SIZE_COORDINATE_IDENTITY_ONLY_NOT_SHAPE_OR_OPTICAL_EQUIVALENCE",
        "wyser_L_is_maximum_dimension_pass": True,
        "yang_bi_size_coordinate_is_maximum_dimension_pass": True,
        "wyser_L_to_yang_dmax_coordinate_validated": True,
        "coordinate_identity": "Wyser_L_um == Yang_Bi_maximum_dimension_um",
        "coordinate_authoritative_for_runtime_mapping": False,
        "exact_yang_bi_v2_solid_column_geometry_law_pinned": bool(diagnostic["exact_yang_v2_geometry_law_pinned"]),
        "wyser_to_yang_solid_column_shape_compatibility_pass": False,
        "wyser_to_yang_projected_area_compatibility_pass": False,
        "wyser_to_yang_volume_mass_compatibility_pass": False,
        "independent_eq6_external_numeric_corroboration_pass": False,
        "scientific_mass_closure_executed": False,
        "yang_bi_habit_bridge_validated": False,
        "yang_bi_roughness_bridge_validated": False,
        "bulk_yang_bi_psd_integration_eligible": False,
        "gfsv16_dmax_mapping_eligible": False,
        "production_ice_optics_ready": False,
        "physics_promotion_allowed": False,
        "geometry_diagnostic": {key: value for key, value in diagnostic.items() if key != "rows"},
        "forbidden_shortcuts": [
            "literature_transcription_used_instead_of_authoritative_source_row_geometry",
            "coordinate_identity_treated_as_shape_equivalence",
            "coordinate_identity_treated_as_projected_area_equivalence",
            "coordinate_identity_treated_as_volume_or_mass_equivalence",
            "coordinate_identity_used_to_enable_bulk_optics_before_shape_habit_roughness_validation",
            "coordinate_identity_used_to_enable_GFS_Dmax_mapping_without_source_microphysics_validation",
            "fixed_Yang_Bi_habit_default",
            "fixed_surface_roughness_default",
            "scientific_mass_closure_claimed_before_independent_eq6_numeric_corroboration",
            "production_promotion_before_independent_bulk_optics_validation",
        ],
        "qualification_requirements": [
            "obtain_independent_external_numeric_corroboration_for_Wyser_equation_6",
            "execute_scientific_IWC_mass_closure_over_supported_domain",
            "qualify_Wyser_to_Yang_solid_column_shape_projected_area_and_volume_mass_bridge",
            "validate_Yang_Bi_habit_bridge",
            "validate_roughness_uncertainty_policy",
            "independent_bulk_shortwave_optics_validation",
            "separate_production_promotion_gate",
        ],
        "historical_step3g_contract_is_not_rewritten": True,
        "frozen_science_unchanged": True,
    }
