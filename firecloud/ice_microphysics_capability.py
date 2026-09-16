"""Ice Optics Phase 2 native-microphysics capability audit.

R5.7.41.3.4.10.13 is diagnostic/readiness only.  This module inspects the
microphysical evidence that already exists in the GFS/CASE pipeline and reports
whether a Dmax or PSD mapping is *eligible* to be attempted.  It must never
invent particle size, PSD, habit, surface roughness, cloud condensate, or a
production optical property.

Frozen science remains R5.7.41.2_SHADOW_COT_AB_FROZEN.
"""
from __future__ import annotations

from typing import Any, Iterable

import numpy as np
import pandas as pd

from .providers.gfs_native import GFS_PROVIDER_SCHEMA_VERSION

SCIENCE_BASELINE = "R5.7.41.2_SHADOW_COT_AB_FROZEN"
ICE_PHASE2_VERSION = "R5.7.41.3.4.10.13"
ICE_PHASE2_MODE = "DIAGNOSTIC_READINESS_ONLY"
PHYSICS_PROMOTION_ALLOWED = False

D_MAX_BLOCKERS = (
    "ICE_DMAX_NATIVE_FIELD_UNAVAILABLE",
    "ICE_DMAX_MAPPING_UNAVAILABLE",
)
PSD_BLOCKERS = ("ICE_PSD_INPUT_INCOMPLETE",)
HABIT_BLOCKERS = ("ICE_HABIT_UNRESOLVED",)
ROUGHNESS_BLOCKERS = ("ICE_ROUGHNESS_UNRESOLVED",)
ALL_MAPPING_BLOCKERS = D_MAX_BLOCKERS + PSD_BLOCKERS + HABIT_BLOCKERS + ROUGHNESS_BLOCKERS

_RAW_FIELDS: tuple[tuple[str, str, str, str, str], ...] = (
    ("ICMR", "cloud_ice_water_kgkg", "NATIVE_GFS", "ICE_MASS_INPUT", "NO_DIRECT_DMAX_OR_PSD_MAPPING"),
    ("CLWMR", "cloud_liquid_water_kgkg", "NATIVE_GFS", "LIQUID_MASS_CONTEXT", "NO_DMAX_OR_PSD_MAPPING"),
    ("SNMR", "snow_water_kgkg", "NATIVE_GFS", "PRECIPITATING_FROZEN_MASS_CONTEXT", "NOT_CLOUD_ICE_DMAX"),
    ("GRLE", "graupel_kgkg", "NATIVE_GFS", "PRECIPITATING_FROZEN_MASS_CONTEXT", "NOT_CLOUD_ICE_DMAX"),
    ("RWMR", "rain_water_kgkg", "NATIVE_GFS", "PRECIPITATION_MASS_CONTEXT", "NO_DMAX_OR_PSD_MAPPING"),
    ("TCDC", "cloud_fraction", "NATIVE_GFS", "CLOUD_FRACTION_CONTEXT", "NO_DMAX_OR_PSD_MAPPING"),
    ("TMP", "temperature_k", "NATIVE_GFS", "THERMODYNAMIC_CONTEXT", "NO_DMAX_OR_PSD_MAPPING"),
    ("RH", "relative_humidity_pct", "NATIVE_GFS", "THERMODYNAMIC_CONTEXT", "NO_DMAX_OR_PSD_MAPPING"),
    ("HGT", "geopotential_height_m", "NATIVE_GFS", "VERTICAL_GEOMETRY_CONTEXT", "NO_DMAX_OR_PSD_MAPPING"),
)

_AUDIT_COLUMNS = [
    "phase2_version", "science_baseline", "phase2_mode", "provider",
    "provider_schema_version", "gfs_run_utc", "gfs_forecast_hour", "gfs_valid_time_utc",
    "field_short_name", "canonical_semantic", "type_of_level", "level", "units",
    "native_message_present", "native_message_count", "decoded_route_value_count",
    "nonnull_count", "positive_count", "native_vs_derived", "source_artifact",
    "source_provenance", "dmax_mapping_role", "psd_mapping_role", "eligibility_state",
    "eligibility_blockers", "physics_promotion_allowed", "notes",
]

_SUMMARY_COLUMNS = [
    "phase2_version", "science_baseline", "phase2_mode",
    "NATIVE_ICE_MASS_INPUT_READY", "NATIVE_THERMODYNAMIC_CONTEXT_READY",
    "NATIVE_VERTICAL_PROFILE_SUPPORT", "NATIVE_DMAX_AVAILABLE",
    "CALIBRATED_DMAX_MAPPING_AVAILABLE", "NATIVE_PSD_AVAILABLE",
    "CALIBRATED_PSD_MAPPING_AVAILABLE", "ICE_HABIT_RESOLUTION_READY",
    "ICE_ROUGHNESS_RESOLUTION_READY", "MICROPHYSICS_MAPPING_READY",
    "SINGLE_PARTICLE_LUT_LOOKUP_ELIGIBLE", "BULK_PSD_SYNTHESIS_ELIGIBLE",
    "PRODUCTION_ICE_OPTICS_READY", "physics_promotion_allowed",
    "positive_iwp_row_count", "runtime_dmax_nonnull_count", "runtime_reff_nonnull_count",
    "runtime_habit_resolved_count", "runtime_roughness_resolved_count",
    "eligibility_state", "eligibility_blockers", "detail",
]


def _frame(value: Any) -> pd.DataFrame:
    return value.copy() if isinstance(value, pd.DataFrame) else pd.DataFrame()


def _numeric(series: pd.Series | Iterable[Any] | None) -> pd.Series:
    if series is None:
        return pd.Series(dtype=float)
    return pd.to_numeric(pd.Series(series), errors="coerce")


def _nonnull_positive(frame: pd.DataFrame, column: str) -> tuple[int, int]:
    if frame.empty or column not in frame.columns:
        return 0, 0
    values = _numeric(frame[column])
    return int(values.notna().sum()), int((values > 0).sum())


def _string_resolved_count(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    s = frame[column].fillna("").astype(str).str.strip()
    bad = {"", "UNKNOWN", "MISSING", "NONE", "NAN", "UNRESOLVED"}
    return int((~s.str.upper().isin(bad)).sum())


def _inventory_subset(inv: pd.DataFrame, short_name: str) -> pd.DataFrame:
    if inv.empty or "shortName" not in inv.columns:
        return pd.DataFrame()
    return inv[inv["shortName"].astype(str).str.upper().eq(str(short_name).upper())].copy()


def _completeness_row(comp: pd.DataFrame, short_name: str) -> pd.Series | None:
    if comp.empty or "field" not in comp.columns:
        return None
    rows = comp[comp["field"].astype(str).str.upper().eq(str(short_name).upper())]
    return None if rows.empty else rows.iloc[0]


def _first_nonblank(frame: pd.DataFrame, column: str) -> Any:
    if frame.empty or column not in frame.columns:
        return None
    for value in frame[column].tolist():
        if pd.notna(value) and str(value).strip() != "":
            return value
    return None


def _route_value_count(comp_row: pd.Series | None, short_name: str) -> float:
    if comp_row is None:
        return np.nan
    candidates = {
        "ICMR": ("icmr_nonnull_route_values",),
        "CLWMR": ("clwmr_nonnull_route_values",),
    }.get(short_name.upper(), ())
    for col in candidates:
        if col in comp_row.index and pd.notna(comp_row.get(col)):
            try:
                return float(comp_row.get(col))
            except Exception:
                pass
    return np.nan


def _row(**kwargs: Any) -> dict[str, Any]:
    base = {c: None for c in _AUDIT_COLUMNS}
    base.update({
        "phase2_version": ICE_PHASE2_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "phase2_mode": ICE_PHASE2_MODE,
        "provider": "NOAA_GFS_0P25_NATIVE_CLOUD",
        "provider_schema_version": GFS_PROVIDER_SCHEMA_VERSION,
        "physics_promotion_allowed": False,
    })
    base.update(kwargs)
    return base


def build_native_microphysics_capability_audit(
    gfs_grib_message_inventory: pd.DataFrame | None,
    gfs_native_field_completeness: pd.DataFrame | None,
    native_cloud_voxel_matrix: pd.DataFrame | None,
    native_cloud_columns: pd.DataFrame | None,
    ice_runtime: pd.DataFrame | None,
) -> pd.DataFrame:
    """Build a CASE-ready evidence audit without synthesizing missing microphysics."""
    inv = _frame(gfs_grib_message_inventory)
    comp = _frame(gfs_native_field_completeness)
    vox = _frame(native_cloud_voxel_matrix)
    cols = _frame(native_cloud_columns)
    rt = _frame(ice_runtime)

    run_utc = _first_nonblank(inv, "gfs_run_utc") or _first_nonblank(comp, "gfs_run_utc")
    lead = _first_nonblank(inv, "gfs_forecast_hour") or _first_nonblank(comp, "gfs_forecast_hour")
    valid_utc = _first_nonblank(inv, "gfs_valid_time_utc") or _first_nonblank(comp, "gfs_valid_time_utc")

    rows: list[dict[str, Any]] = []
    for short_name, semantic, origin, role, mapping_note in _RAW_FIELDS:
        sub = _inventory_subset(inv, short_name)
        crow = _completeness_row(comp, short_name)
        msg_count = 0
        if not sub.empty and "message_count" in sub.columns:
            msg_count = int(pd.to_numeric(sub["message_count"], errors="coerce").fillna(0).sum())
        elif crow is not None and pd.notna(crow.get("message_count")):
            msg_count = int(crow.get("message_count") or 0)
        native_present = bool(msg_count > 0 or (crow is not None and str(crow.get("status", "")).upper() == "READY"))
        types = "|".join(sorted({str(x) for x in sub.get("typeOfLevel", pd.Series(dtype=object)).dropna().tolist()}))
        levels = pd.to_numeric(sub.get("level", pd.Series(dtype=float)), errors="coerce").dropna().tolist()
        level_repr = "|".join(str(int(x) if float(x).is_integer() else float(x)) for x in sorted(set(levels)))
        units = "|".join(sorted({str(x) for x in sub.get("units", pd.Series(dtype=object)).dropna().tolist() if str(x).strip()}))
        blockers = []
        dmax_role = "NOT_ELIGIBLE_AS_DMAX"
        psd_role = "NOT_ELIGIBLE_AS_PSD"
        if short_name == "ICMR":
            dmax_role = "MASS_INPUT_ONLY_NO_SIZE_SEMANTICS"
            psd_role = "BULK_MASS_ONLY_INSUFFICIENT_FOR_PSD"
            blockers = list(D_MAX_BLOCKERS + PSD_BLOCKERS)
        elif short_name in {"TMP", "RH", "TCDC", "HGT", "CLWMR", "SNMR", "GRLE", "RWMR"}:
            blockers = list(D_MAX_BLOCKERS + PSD_BLOCKERS)
        rows.append(_row(
            gfs_run_utc=run_utc, gfs_forecast_hour=lead, gfs_valid_time_utc=valid_utc,
            field_short_name=short_name, canonical_semantic=semantic,
            type_of_level=types or None, level=level_repr or None, units=units or None,
            native_message_present=native_present, native_message_count=msg_count,
            decoded_route_value_count=_route_value_count(crow, short_name),
            nonnull_count=np.nan, positive_count=np.nan, native_vs_derived=origin,
            source_artifact="gfs_grib_message_inventory.csv|gfs_native_field_completeness.csv",
            source_provenance="GFS GRIB inventory/completeness; native field semantics only",
            dmax_mapping_role=dmax_role, psd_mapping_role=psd_role,
            eligibility_state="NATIVE_INPUT_AVAILABLE_NO_PARTICLE_SIZE_SEMANTICS" if native_present else "NATIVE_INPUT_NOT_PROVEN_IN_CASE",
            eligibility_blockers="|".join(blockers),
            notes=f"{role}; {mapping_note}. Presence does not authorize Dmax/PSD synthesis.",
        ))

    derived_specs = (
        ("DERIVED_IWC", "ice_water_content_gm3", vox, "ice_water_content_gm3", "g/m3", "native_gfs_cloud_voxel_3d.csv", "Deterministic ICMR * air-density conversion"),
        ("DERIVED_IWP", "ice_water_path_proxy_gm3_km", cols, "ice_water_path_proxy_gm3_km", "kg/m2 numeric identity when vertically complete", "native_gfs_cloud_columns.csv", "Deterministic vertical integration of IWC; not a GFS native field"),
        ("VERTICAL_COMPLETENESS", "native_vertical_completeness", cols, "native_vertical_completeness", "fraction", "native_gfs_cloud_columns.csv", "Deterministic support/completeness diagnostic"),
    )
    for short_name, semantic, frame, column, units, artifact, provenance in derived_specs:
        nonnull, positive = _nonnull_positive(frame, column)
        rows.append(_row(
            gfs_run_utc=run_utc, gfs_forecast_hour=lead, gfs_valid_time_utc=valid_utc,
            field_short_name=short_name, canonical_semantic=semantic, units=units,
            native_message_present=False, native_message_count=0,
            decoded_route_value_count=np.nan, nonnull_count=nonnull, positive_count=positive,
            native_vs_derived="DETERMINISTIC_DERIVED",
            source_artifact=artifact, source_provenance=provenance,
            dmax_mapping_role="NOT_ELIGIBLE_AS_DMAX_WITHOUT_SEPARATE_CALIBRATED_MAPPING",
            psd_mapping_role="NOT_ELIGIBLE_AS_PSD_WITHOUT_SEPARATE_CALIBRATED_MAPPING",
            eligibility_state="DERIVED_CONTEXT_ONLY",
            eligibility_blockers="|".join(D_MAX_BLOCKERS + PSD_BLOCKERS),
            notes="Derived evidence may constrain a future calibrated mapping but cannot create particle size/PSD by itself.",
        ))

    runtime_specs = (
        ("RUNTIME_DMAX", "ice_maximum_dimension_um", "ice_maximum_dimension_um", "um", "Dmax runtime slot", "ICE_DMAX_NATIVE_FIELD_UNAVAILABLE|ICE_DMAX_MAPPING_UNAVAILABLE"),
        ("RUNTIME_REFF", "ice_effective_radius_um", "ice_effective_radius_um", "um", "diagnostic metadata only; never Dmax substitute", "ICE_DMAX_NATIVE_FIELD_UNAVAILABLE|ICE_DMAX_MAPPING_UNAVAILABLE"),
    )
    for short_name, semantic, column, units, note, blockers in runtime_specs:
        nonnull, positive = _nonnull_positive(rt, column)
        rows.append(_row(
            gfs_run_utc=run_utc, gfs_forecast_hour=lead, gfs_valid_time_utc=valid_utc,
            field_short_name=short_name, canonical_semantic=semantic, units=units,
            native_message_present=False, native_message_count=0, decoded_route_value_count=np.nan,
            nonnull_count=nonnull, positive_count=positive, native_vs_derived="RUNTIME_SLOT",
            source_artifact="v1_ice_cloud_spectral_optics_runtime.csv",
            source_provenance="Ice optics runtime slot; not proof of GFS native semantics",
            dmax_mapping_role="AUTHORITATIVE_AXIS_ONLY_IF_SEPARATELY_PROVEN" if short_name == "RUNTIME_DMAX" else "FORBIDDEN_AS_DMAX_SUBSTITUTE",
            psd_mapping_role="NOT_A_PSD",
            eligibility_state="RUNTIME_SLOT_PRESENT_BUT_NATIVE_OR_CALIBRATED_PROVENANCE_REQUIRED" if nonnull else "RUNTIME_SLOT_UNPOPULATED",
            eligibility_blockers=blockers,
            notes=note,
        ))

    for short_name, semantic, column, blocker in (
        ("RUNTIME_HABIT", "ice_habit", "ice_habit", "ICE_HABIT_UNRESOLVED"),
        ("RUNTIME_ROUGHNESS", "surface_roughness", "surface_roughness", "ICE_ROUGHNESS_UNRESOLVED"),
    ):
        resolved = _string_resolved_count(rt, column)
        rows.append(_row(
            gfs_run_utc=run_utc, gfs_forecast_hour=lead, gfs_valid_time_utc=valid_utc,
            field_short_name=short_name, canonical_semantic=semantic,
            native_message_present=False, native_message_count=0, decoded_route_value_count=np.nan,
            nonnull_count=resolved, positive_count=np.nan, native_vs_derived="RUNTIME_SLOT",
            source_artifact="v1_ice_cloud_spectral_optics_runtime.csv",
            source_provenance="Ice optics runtime slot; current GFS provider does not supply this semantic",
            dmax_mapping_role="REQUIRED_CONTEXT_NOT_DMAX", psd_mapping_role="REQUIRED_CONTEXT_NOT_PSD",
            eligibility_state="RUNTIME_CONTEXT_UNRESOLVED" if resolved == 0 else "RUNTIME_VALUE_PRESENT_PROVENANCE_STILL_REQUIRED",
            eligibility_blockers=blocker,
            notes="No fixed/default/proxy rule is authorized in R5.7.41.3.4.10.13.",
        ))

    for short_name, semantic, note in (
        ("PSD_SIZE_BINS", "particle_size_distribution_bins", "No native cloud-ice particle size bins are requested/decoded by the current GFS ingest."),
        ("PSD_NUMBER_CONCENTRATION", "ice_particle_number_concentration", "No native cloud-ice number concentration is requested/decoded by the current GFS ingest."),
        ("PSD_MOMENTS", "particle_size_distribution_moments_or_parameters", "ICMR/IWP/T/RH/TCDC/cloud thickness are not sufficient PSD moments."),
    ):
        rows.append(_row(
            gfs_run_utc=run_utc, gfs_forecast_hour=lead, gfs_valid_time_utc=valid_utc,
            field_short_name=short_name, canonical_semantic=semantic,
            native_message_present=False, native_message_count=0, decoded_route_value_count=np.nan,
            nonnull_count=0, positive_count=0, native_vs_derived="MISSING_CAPABILITY",
            source_artifact="GFS ingest schema + CASE evidence",
            source_provenance="Capability absence audit",
            dmax_mapping_role="NO_DMAX_EVIDENCE", psd_mapping_role="REQUIRED_FOR_NATIVE_PSD_BUT_UNAVAILABLE",
            eligibility_state="INSUFFICIENT_PSD_INPUTS", eligibility_blockers="ICE_PSD_INPUT_INCOMPLETE",
            notes=note,
        ))

    return pd.DataFrame(rows, columns=_AUDIT_COLUMNS)


def build_mapping_eligibility_summary(
    audit: pd.DataFrame | None,
    native_cloud_columns: pd.DataFrame | None,
    ice_runtime: pd.DataFrame | None,
) -> pd.DataFrame:
    """Return the explicit fail-closed Phase-2 mapping gate for the current run."""
    a = _frame(audit)
    cols = _frame(native_cloud_columns)
    rt = _frame(ice_runtime)

    def _raw_ready(field: str) -> bool:
        if a.empty:
            return False
        rows = a[a["field_short_name"].astype(str).eq(field)]
        return bool((rows.get("native_message_present", pd.Series(dtype=bool)).fillna(False).astype(bool)).any())

    iwp = _numeric(cols["ice_water_path_proxy_gm3_km"]) if "ice_water_path_proxy_gm3_km" in cols.columns else pd.Series(dtype=float)
    completeness = _numeric(cols["native_vertical_completeness"]) if "native_vertical_completeness" in cols.columns else pd.Series(dtype=float)
    dmax_nonnull, _ = _nonnull_positive(rt, "ice_maximum_dimension_um")
    reff_nonnull, _ = _nonnull_positive(rt, "ice_effective_radius_um")
    habit_resolved = _string_resolved_count(rt, "ice_habit")
    rough_resolved = _string_resolved_count(rt, "surface_roughness")

    native_mass_ready = _raw_ready("ICMR")
    thermo_ready = _raw_ready("TMP")
    vertical_support = bool(completeness.notna().any() and (completeness > 0).any())

    # Deliberately false until an explicit, separately-reviewed source contract
    # proves the corresponding semantic.  Runtime slot population alone is not proof.
    native_dmax_available = False
    calibrated_dmax_mapping_available = False
    native_psd_available = False
    calibrated_psd_mapping_available = False
    habit_ready = False
    roughness_ready = False

    single_lookup = bool((native_dmax_available or calibrated_dmax_mapping_available) and habit_ready and roughness_ready)
    bulk_psd = bool((native_psd_available or calibrated_psd_mapping_available) and native_mass_ready and vertical_support and habit_ready and roughness_ready)
    # A future implementation may become eligible through either an explicitly
    # proven single-particle Dmax path or an explicitly proven bulk PSD path;
    # Phase 2 does not require both at once.  In .10.12 both remain false.
    mapping_ready = bool(single_lookup or bulk_psd)
    blockers = list(ALL_MAPPING_BLOCKERS)

    rec = {
        "phase2_version": ICE_PHASE2_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "phase2_mode": ICE_PHASE2_MODE,
        "NATIVE_ICE_MASS_INPUT_READY": native_mass_ready,
        "NATIVE_THERMODYNAMIC_CONTEXT_READY": thermo_ready,
        "NATIVE_VERTICAL_PROFILE_SUPPORT": vertical_support,
        "NATIVE_DMAX_AVAILABLE": native_dmax_available,
        "CALIBRATED_DMAX_MAPPING_AVAILABLE": calibrated_dmax_mapping_available,
        "NATIVE_PSD_AVAILABLE": native_psd_available,
        "CALIBRATED_PSD_MAPPING_AVAILABLE": calibrated_psd_mapping_available,
        "ICE_HABIT_RESOLUTION_READY": habit_ready,
        "ICE_ROUGHNESS_RESOLUTION_READY": roughness_ready,
        "MICROPHYSICS_MAPPING_READY": mapping_ready,
        "SINGLE_PARTICLE_LUT_LOOKUP_ELIGIBLE": single_lookup,
        "BULK_PSD_SYNTHESIS_ELIGIBLE": bulk_psd,
        "PRODUCTION_ICE_OPTICS_READY": False,
        "physics_promotion_allowed": False,
        "positive_iwp_row_count": int((iwp > 1e-15).sum()),
        "runtime_dmax_nonnull_count": dmax_nonnull,
        "runtime_reff_nonnull_count": reff_nonnull,
        "runtime_habit_resolved_count": habit_resolved,
        "runtime_roughness_resolved_count": rough_resolved,
        "eligibility_state": "INSUFFICIENT_MICROPHYSICS",
        "eligibility_blockers": "|".join(blockers),
        "detail": "ICMR/IWP/T/RH/TCDC/cloud geometry cannot auto-create Dmax, PSD, habit, or roughness; Phase 2 remains diagnostic-only.",
    }
    return pd.DataFrame([rec], columns=_SUMMARY_COLUMNS)


def phase2_contract_payload(*, physicscore_version: str) -> dict[str, Any]:
    """Machine-readable mapping eligibility contract included in every CASE."""
    return {
        "contract_version": "FIRECLOUD_ICE_MICROPHYSICS_PHASE2_ELIGIBILITY_V1",
        "phase2_version": ICE_PHASE2_VERSION,
        "physicscore_version": str(physicscore_version),
        "science_baseline": SCIENCE_BASELINE,
        "mode": ICE_PHASE2_MODE,
        "physics_promotion_allowed": False,
        "authoritative_runtime_size_axis": "maximum_dimension_um",
        "forbidden_implicit_mappings": [
            "effective_radius_um_to_maximum_dimension_um",
            "CER_to_Dmax", "IWP_to_Dmax", "temperature_to_Dmax",
            "cloud_thickness_to_Dmax", "RH_to_Dmax", "TCDC_to_Dmax",
            "temperature_or_cloud_regime_to_habit", "fixed_habit_default",
            "fixed_surface_roughness_default", "assumed_PSD_without_source_contract",
        ],
        "current_mapping_blockers": list(ALL_MAPPING_BLOCKERS),
        "native_dmax_eligibility_requires": [
            "raw provider field or CASE-traceable raw field",
            "semantics compatible with Yang/Bi maximum particle dimension",
            "units directly convertible to micrometres without physical assumptions",
            "complete run/cycle/valid-time/level/provider provenance",
            "finite positive values for the cloud-ice population",
        ],
        "calibrated_mapping_requires": [
            "versioned external source or literature/model provenance",
            "mapping inputs actually present in the current CASE",
            "explicit validity domain and fail-close outside domain",
            "uncertainty representation",
            "synthetic QA plus independent validation",
            "no hidden climatological/default substitution",
            "separate science promotion gate",
        ],
        "current_default_positive_iwp_state": "INSUFFICIENT_MICROPHYSICS",
        "frozen_science_unchanged": True,
    }
