"""Ice Optics Phase 2 Step 3P — Yang/Bi full-spectral source qualification.

This qualification asks whether authoritative Yang/Bi V2 *source bytes* are
available for broad-band integration work.  It does not synthesize a spectrum
from the portable six-band LUT and it does not claim Fu96/RRTMG weighting is
known.  Missing source bytes are a valid, deterministic fail-closed state.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import math

import numpy as np
import pandas as pd

from . import __version__ as PHYSICSCORE_VERSION
from .ice_optics_authoritative import (
    SOURCE_ZENODO_RECORD,
    SOURCE_ARCHIVE_SHORTWAVE,
    SOURCE_ARCHIVE_SHORTWAVE_MD5,
    SOURCE_EXPECTED_WAVELENGTH_COUNT,
    SOURCE_EXPECTED_SIZE_COUNT,
    SOURCE_EXPECTED_ISCA_ROWS,
    SOURCE_SHORTWAVE_RANGE_UM,
    resolve_isca_path,
    inspect_isca_file,
)

SCIENCE_BASELINE = "R5.7.41.2_SHADOW_COT_AB_FROZEN"
STEP3P_VERSION = "R5.7.41.3.4.10.29"
STEP3P_MODE = "YANG_FULL_SPECTRAL_SOURCE_CAPABILITY_QUALIFICATION_FAIL_CLOSED"
EVIDENCE_AS_OF = "2026-09-18"
REFERENCE_HABIT = "single_column"
ROUGHNESS_STATES = ("Rough000", "Rough003", "Rough050")
RRTMG_BAND_DOMAINS_UM = {
    25: (1.0e4 / 22650.0, 1.0e4 / 16000.0),
    24: (1.0e4 / 16000.0, 1.0e4 / 12850.0),
}


def _band_domain_coverage(raw: pd.DataFrame | None, band: int) -> dict[str, Any]:
    low, high = RRTMG_BAND_DOMAINS_UM[int(band)]
    if raw is None or raw.empty or "wavelength_um" not in raw.columns:
        return {
            "rrtmg_band": int(band),
            "band_low_um": float(low),
            "band_high_um": float(high),
            "source_points_inside_band": 0,
            "source_min_um": None,
            "source_max_um": None,
            "domain_covered": False,
        }
    x = np.asarray(sorted(pd.to_numeric(raw["wavelength_um"], errors="coerce").dropna().unique()), dtype=float)
    inside = x[(x >= low) & (x <= high)]
    covered = bool(len(x) >= 2 and float(x.min()) <= low and float(x.max()) >= high and len(inside) >= 2)
    return {
        "rrtmg_band": int(band),
        "band_low_um": float(low),
        "band_high_um": float(high),
        "source_points_inside_band": int(len(inside)),
        "source_min_um": float(x.min()) if len(x) else None,
        "source_max_um": float(x.max()) if len(x) else None,
        "domain_covered": covered,
    }


def _row(check_id: str, category: str, status: str, observed: str, required: str, notes: str = "") -> dict[str, Any]:
    return {
        "check_id": check_id,
        "category": category,
        "status": status,
        "observed": observed,
        "required": required,
        "physics_promotion_allowed": False,
        "notes": notes,
    }


def _scan_source(source_root: str | Path | None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "source_root_supplied": source_root is not None,
        "source_bytes_available": False,
        "all_source_files_valid": False,
        "band24_coverage_pass": False,
        "band25_coverage_pass": False,
        "records": [],
    }
    if source_root is None:
        return result
    root = Path(source_root).expanduser()
    band24 = []
    band25 = []
    valid = []
    for roughness in ROUGHNESS_STATES:
        path = resolve_isca_path(root, REFERENCE_HABIT, roughness)
        rec, raw = inspect_isca_file(path, ice_habit=REFERENCE_HABIT, surface_roughness=roughness)
        c24 = _band_domain_coverage(raw, 24)
        c25 = _band_domain_coverage(raw, 25)
        result["records"].append({
            "surface_roughness": roughness,
            "exists": bool(rec.exists),
            "status": str(rec.status),
            "row_count": rec.row_count,
            "wavelength_count": rec.wavelength_count,
            "particle_size_count": rec.particle_size_count,
            "source_sha256": rec.source_sha256,
            "band24": c24,
            "band25": c25,
        })
        valid.append(bool(rec.exists and rec.status == "PASS"))
        band24.append(bool(rec.exists and rec.status == "PASS" and c24["domain_covered"]))
        band25.append(bool(rec.exists and rec.status == "PASS" and c25["domain_covered"]))
    result["source_bytes_available"] = bool(all(r["exists"] for r in result["records"]))
    result["all_source_files_valid"] = bool(all(valid))
    result["band24_coverage_pass"] = bool(all(band24))
    result["band25_coverage_pass"] = bool(all(band25))
    return result


def build_yang_full_spectral_source_qualification_evidence(source_root: str | Path | None = None) -> pd.DataFrame:
    scan = _scan_source(source_root)
    rows = [
        _row(
            "YANG_V2_FULL_SPECTRAL_SOURCE_CONTRACT",
            "SOURCE_CONTRACT",
            "PASS_PINNED",
            f"396 wavelengths; 189 sizes; expected isca rows={SOURCE_EXPECTED_ISCA_ROWS}",
            "AUTHORITATIVE_SOURCE_CONTRACT_PINNED",
            f"Zenodo {SOURCE_ZENODO_RECORD}; archive {SOURCE_ARCHIVE_SHORTWAVE}; published MD5 {SOURCE_ARCHIVE_SHORTWAVE_MD5}",
        ),
        _row(
            "YANG_V2_FULL_SPECTRAL_SOURCE_BYTES",
            "SOURCE_AVAILABILITY",
            "PASS_AVAILABLE" if scan["source_bytes_available"] else "SOURCE_BYTES_UNAVAILABLE",
            str(bool(scan["source_bytes_available"])).lower(),
            "EXPLICIT_SOURCE_ROOT_AND_THREE_SINGLE_COLUMN_ROUGHNESS_FILES",
            "Release package intentionally does not invent or embed missing authoritative bytes.",
        ),
    ]
    record_map = {r["surface_roughness"]: r for r in scan["records"]}
    for roughness in ROUGHNESS_STATES:
        rec = record_map.get(roughness)
        rows.append(_row(
            f"YANG_SINGLE_COLUMN_{roughness.upper()}_FULL_SPECTRAL_FILE",
            "SOURCE_FILE_QUALIFICATION",
            ("PASS" if rec and rec["status"] == "PASS" else (rec["status"] if rec else "SOURCE_BYTES_UNAVAILABLE")),
            (
                f"rows={rec['row_count']}; wavelengths={rec['wavelength_count']}; sizes={rec['particle_size_count']}"
                if rec else "source root not supplied"
            ),
            f"rows={SOURCE_EXPECTED_ISCA_ROWS}; wavelengths={SOURCE_EXPECTED_WAVELENGTH_COUNT}; sizes={SOURCE_EXPECTED_SIZE_COUNT}",
            "Source-row geometry may vary by wavelength under the frozen authoritative-source policy.",
        ))
    rows.extend([
        _row(
            "RRTMG_BAND24_YANG_SPECTRAL_DOMAIN_COVERAGE",
            "SPECTRAL_DOMAIN",
            "PASS" if scan["band24_coverage_pass"] else "BLOCKED_SOURCE_UNAVAILABLE_OR_INVALID",
            str(bool(scan["band24_coverage_pass"])).lower(),
            f"Yang source spans {RRTMG_BAND_DOMAINS_UM[24][0]:.9g}-{RRTMG_BAND_DOMAINS_UM[24][1]:.9g} um for all three roughness states",
            "Domain coverage is not equivalent to Fu96/RRTMG band weighting.",
        ),
        _row(
            "RRTMG_BAND25_YANG_SPECTRAL_DOMAIN_COVERAGE",
            "SPECTRAL_DOMAIN",
            "PASS" if scan["band25_coverage_pass"] else "BLOCKED_SOURCE_UNAVAILABLE_OR_INVALID",
            str(bool(scan["band25_coverage_pass"])).lower(),
            f"Yang source spans {RRTMG_BAND_DOMAINS_UM[25][0]:.9g}-{RRTMG_BAND_DOMAINS_UM[25][1]:.9g} um for all three roughness states",
            "Domain coverage is not equivalent to Fu96/RRTMG band weighting.",
        ),
        _row(
            "PORTABLE_SIX_BAND_LUT_FULL_SPECTRAL_SUBSTITUTE",
            "SCOPE_GUARD",
            "PASS_FORBIDDEN",
            "false",
            "SIX_MONOCHROMATIC_POINTS_MUST_NOT_BE_EXPANDED_TO_SYNTHETIC_396_WAVE_SOURCE",
        ),
        _row(
            "EXACT_FU96_RRTMG_BAND_WEIGHTING",
            "BAND_WEIGHTING_BLOCKER",
            "BLOCKED_NOT_PROVEN",
            "false",
            "EXACT_PRIMARY_OR_AUTHORITATIVE_BAND_AVERAGING_WEIGHTING_REQUIRED",
        ),
        _row(
            "INDEPENDENT_SSA_ASYMMETRY_VALIDATION",
            "VALIDATION_BLOCKER",
            "BLOCKED",
            "false",
            "FULL_SPECTRAL_SOURCE_PLUS_EXACT_WEIGHTING_PLUS_NUMERIC_ACCEPTANCE_REQUIRED",
        ),
        _row(
            "PRODUCTION_PROMOTION_GUARD",
            "PRODUCTION_GUARD",
            "PASS_FAIL_CLOSED",
            "tau_ice=false; production_ice_optics=false; physics_promotion=false",
            "NO_STEP3P_PRODUCTION_PROMOTION",
        ),
    ])
    return pd.DataFrame(rows)


def _status(evidence: pd.DataFrame, check_id: str) -> str:
    m = evidence.loc[evidence["check_id"].astype(str) == check_id, "status"]
    return str(m.iloc[0]) if len(m) else "MISSING"


def build_yang_full_spectral_source_qualification_gate(evidence: pd.DataFrame) -> pd.DataFrame:
    source_available = _status(evidence, "YANG_V2_FULL_SPECTRAL_SOURCE_BYTES") == "PASS_AVAILABLE"
    b24 = _status(evidence, "RRTMG_BAND24_YANG_SPECTRAL_DOMAIN_COVERAGE") == "PASS"
    b25 = _status(evidence, "RRTMG_BAND25_YANG_SPECTRAL_DOMAIN_COVERAGE") == "PASS"
    state = (
        "PASS_FAIL_CLOSED_WEIGHTING_PENDING" if source_available and b24 and b25
        else "PASS_FAIL_CLOSED_SOURCE_BYTES_UNAVAILABLE"
    )
    return pd.DataFrame([{
        "qualification_state": state,
        "YANG_FULL_SPECTRAL_SOURCE_CONTRACT_PINNED": True,
        "YANG_FULL_SPECTRAL_SOURCE_BYTES_AVAILABLE": bool(source_available),
        "RRTMG_BAND24_SPECTRAL_COVERAGE_PASS": bool(b24),
        "RRTMG_BAND25_SPECTRAL_COVERAGE_PASS": bool(b25),
        "EXACT_FU96_BAND_WEIGHTING_AVAILABLE": False,
        "BAND_INTEGRATED_OPTICAL_VALIDATION_READY": False,
        "INDEPENDENT_SSA_VALIDATION_PASS": False,
        "INDEPENDENT_ASYMMETRY_VALIDATION_PASS": False,
        "FULL_SIX_BAND_LIKE_FOR_LIKE_OPTICAL_VALIDATION_PASS": False,
        "TAU_ICE_PRODUCTION_ALLOWED": False,
        "PRODUCTION_ICE_OPTICS_READY": False,
        "physics_promotion_allowed": False,
    }])


def yang_full_spectral_source_qualification_contract_payload(
    *,
    evidence: pd.DataFrame | None = None,
    gate: pd.DataFrame | None = None,
    physicscore_version: str = PHYSICSCORE_VERSION,
) -> dict[str, Any]:
    evidence = evidence if evidence is not None else build_yang_full_spectral_source_qualification_evidence()
    gate = gate if gate is not None else build_yang_full_spectral_source_qualification_gate(evidence)
    g = gate.iloc[0].to_dict()
    return {
        "contract_version": "FIRECLOUD_ICE_YANG_FULL_SPECTRAL_SOURCE_QUALIFICATION_V1",
        "physicscore_version": str(physicscore_version),
        "step_version": STEP3P_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "mode": STEP3P_MODE,
        "evidence_as_of": EVIDENCE_AS_OF,
        "source_contract": {
            "zenodo_record": SOURCE_ZENODO_RECORD,
            "archive": SOURCE_ARCHIVE_SHORTWAVE,
            "published_md5": SOURCE_ARCHIVE_SHORTWAVE_MD5,
            "expected_wavelength_count": SOURCE_EXPECTED_WAVELENGTH_COUNT,
            "expected_size_count": SOURCE_EXPECTED_SIZE_COUNT,
            "expected_isca_rows": SOURCE_EXPECTED_ISCA_ROWS,
            "shortwave_range_um": [float(SOURCE_SHORTWAVE_RANGE_UM[0]), float(SOURCE_SHORTWAVE_RANGE_UM[1])],
            "habit": REFERENCE_HABIT,
            "roughness_states": list(ROUGHNESS_STATES),
        },
        "rrtmg_band_domains_um": {str(k): [float(v[0]), float(v[1])] for k, v in sorted(RRTMG_BAND_DOMAINS_UM.items())},
        "qualification_state": str(g["qualification_state"]),
        "capabilities": {k: bool(v) for k, v in g.items() if k != "qualification_state"},
        "production_guards": {
            "tau_ice_production_allowed": False,
            "production_ice_optics_ready": False,
            "physics_promotion_allowed": False,
        },
        "scope_note": "Source coverage qualification only. Exact Fu96/RRTMG band weighting and optical validation remain blocked.",
    }


def serialize_yang_full_spectral_source_qualification_contract_json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
