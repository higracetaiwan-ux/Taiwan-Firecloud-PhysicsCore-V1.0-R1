from __future__ import annotations

"""Authoritative Yang/Bi V2 ice-optics source intake and QA pipeline.

This module does *not* invent optical coefficients.  It only converts a local,
user-supplied copy of the published Yang/Bi V2 single-scattering database into
Firecloud's six-band ice-optics LUT after explicit source and output QA.

The source record used by this contract is Zenodo record 5348402, whose README
states that the 0.2-15.25 um archive contains 396 wavelengths, 189 particle
sizes, nine habits, three surface-roughness states, and one 74844-row isca.dat
for every habit/roughness pair.
"""

from dataclasses import asdict, dataclass
from hashlib import md5, sha256
from pathlib import Path
from typing import Any, Iterable
import json
import math

import numpy as np
import pandas as pd

from .ice_cloud_spectral_optics import (
    ICE_OPTICS_WAVELENGTHS_NM,
    LUT_REQUIRED_COLUMNS,
    normalize_tamu_isca_frame,
    read_tamu_isca_dat,
    validate_ice_optics_lut,
)

AUTHORITATIVE_SOURCE_CONTRACT_VERSION = "FIRECLOUD_ICE_OPTICS_TAMU_V2_SOURCE_V1"
AUTHORITATIVE_BUILD_GATE_VERSION = "FIRECLOUD_ICE_OPTICS_AUTHORITATIVE_BUILD_GATE_V1"
SOURCE_DATASET = "TAMU_ICE_SINGLE_SCATTERING_V2"
SOURCE_VERSION = "Yang2013_Bi2017_V2"
SOURCE_ZENODO_RECORD = "5348402"
SOURCE_ARCHIVE_SHORTWAVE = "Data_0.2_15.25.tar.gz"
SOURCE_ARCHIVE_SHORTWAVE_MD5 = "2fb9bbab2c2c735a869c863a680e2f70"
SOURCE_ARCHIVE_SHORTWAVE_SIZE_BYTES = 27_400_000_000  # descriptive only; do not gate exact bytes
SOURCE_README = "README_0.2-99um.txt"
SOURCE_README_MD5 = "50ae2be17e08bdccda9a5f5f3b194936"
SOURCE_EXPECTED_WAVELENGTH_COUNT = 396
SOURCE_EXPECTED_SIZE_COUNT = 189
SOURCE_EXPECTED_ISCA_ROWS = SOURCE_EXPECTED_WAVELENGTH_COUNT * SOURCE_EXPECTED_SIZE_COUNT
SOURCE_SHORTWAVE_RANGE_UM = (0.2, 15.25)
SOURCE_PARTICLE_SIZE_RANGE_UM = (2.0, 10000.0)

HABITS: tuple[str, ...] = (
    "single_column",
    "plate",
    "HC",
    "droxtal",
    "HBR",
    "SBR",
    "8_columns",
    "5_plates",
    "10_plates",
)
ROUGHNESS_STATES: tuple[str, ...] = ("Rough000", "Rough003", "Rough050")

# Geometry in isca.dat should be particle geometry rather than a spectral
# property.  Allow tiny text/round-off differences while still detecting a
# malformed source extraction.
GEOMETRY_RELATIVE_SPREAD_TOLERANCE = 1.0e-6


@dataclass(frozen=True)
class SourceFileRecord:
    ice_habit: str
    surface_roughness: str
    path: str
    exists: bool
    row_count: int | None = None
    wavelength_count: int | None = None
    particle_size_count: int | None = None
    min_wavelength_um: float | None = None
    max_wavelength_um: float | None = None
    min_maximum_dimension_um: float | None = None
    max_maximum_dimension_um: float | None = None
    geometry_consistent: bool | None = None
    source_sha256: str | None = None
    status: str = "UNINSPECTED"
    detail: str = ""


@dataclass(frozen=True)
class AuthoritativeBuildResult:
    lut: pd.DataFrame
    source_inventory: pd.DataFrame
    spectral_grid_audit: pd.DataFrame
    qa_summary: dict[str, Any]

    @property
    def ready(self) -> bool:
        return str(self.qa_summary.get("overall_status", "")) == "PASS"


def authoritative_source_manifest() -> dict[str, Any]:
    return {
        "source_contract_version": AUTHORITATIVE_SOURCE_CONTRACT_VERSION,
        "build_gate_version": AUTHORITATIVE_BUILD_GATE_VERSION,
        "source_dataset": SOURCE_DATASET,
        "source_version": SOURCE_VERSION,
        "zenodo_record": SOURCE_ZENODO_RECORD,
        "zenodo_url": f"https://zenodo.org/records/{SOURCE_ZENODO_RECORD}",
        "shortwave_archive": {
            "filename": SOURCE_ARCHIVE_SHORTWAVE,
            "md5": SOURCE_ARCHIVE_SHORTWAVE_MD5,
            "spectral_range_um": list(SOURCE_SHORTWAVE_RANGE_UM),
            "wavelength_count": SOURCE_EXPECTED_WAVELENGTH_COUNT,
        },
        "readme": {"filename": SOURCE_README, "md5": SOURCE_README_MD5},
        "habits": list(HABITS),
        "roughness_states": list(ROUGHNESS_STATES),
        "particle_size_count": SOURCE_EXPECTED_SIZE_COUNT,
        "particle_size_range_um": list(SOURCE_PARTICLE_SIZE_RANGE_UM),
        "expected_isca_rows_per_habit_roughness": SOURCE_EXPECTED_ISCA_ROWS,
        "expected_isca_file_count": len(HABITS) * len(ROUGHNESS_STATES),
        "firecloud_target_wavelengths_nm": list(ICE_OPTICS_WAVELENGTHS_NM),
        "physics_promotion_allowed": False,
        "missing_semantics": "Missing != Clear != Zero; source incompleteness fails closed.",
        "references": [
            "Yang et al. 2013, J. Atmos. Sci. 70, 330-347, DOI 10.1175/JAS-D-12-039.1",
            "Bi & Yang 2017, JQSRT 189, 228-237",
        ],
    }


def _sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    h = sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def md5_file(path: str | Path, *, chunk_size: int = 4 * 1024 * 1024) -> str:
    h = md5()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_shortwave_archive_md5(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {
            "filename": str(p),
            "exists": False,
            "expected_md5": SOURCE_ARCHIVE_SHORTWAVE_MD5,
            "actual_md5": None,
            "status": "MISSING",
        }
    actual = md5_file(p)
    return {
        "filename": str(p),
        "exists": True,
        "byte_size": p.stat().st_size,
        "expected_md5": SOURCE_ARCHIVE_SHORTWAVE_MD5,
        "actual_md5": actual,
        "status": "PASS" if actual.lower() == SOURCE_ARCHIVE_SHORTWAVE_MD5 else "FAIL",
    }


def _candidate_source_roots(root: Path) -> list[Path]:
    """Return source roots that may directly contain habit directories."""
    candidates = [root, root / "Data_0.2_15.25"]
    # Some extractions create one outer directory named after the archive.
    if root.exists():
        for child in root.iterdir():
            if child.is_dir() and child.name.startswith("Data_0.2_15.25"):
                candidates.append(child)
    seen: set[str] = set()
    out: list[Path] = []
    for c in candidates:
        key = str(c.resolve()) if c.exists() else str(c)
        if key not in seen:
            seen.add(key)
            out.append(c)
    return out


def resolve_isca_path(root: str | Path, ice_habit: str, surface_roughness: str) -> Path:
    base = Path(root).expanduser()
    for candidate in _candidate_source_roots(base):
        p = candidate / ice_habit / surface_roughness / "isca.dat"
        if p.exists():
            return p
    # Return canonical expected path even if absent, for actionable audit output.
    return base / "Data_0.2_15.25" / ice_habit / surface_roughness / "isca.dat"


def _relative_spread(values: pd.Series) -> float:
    arr = pd.to_numeric(values, errors="coerce").dropna().to_numpy(dtype=float)
    if len(arr) == 0:
        return float("nan")
    mean = float(np.mean(np.abs(arr)))
    if mean == 0:
        return 0.0 if float(np.ptp(arr)) == 0 else float("inf")
    return float(np.ptp(arr) / mean)


def _geometry_consistency(raw: pd.DataFrame) -> tuple[bool, float, float]:
    max_v_spread = 0.0
    max_a_spread = 0.0
    for _, g in raw.groupby("maximum_dimension_um", sort=False):
        v = _relative_spread(g["volume_um3"])
        a = _relative_spread(g["projected_area_um2"])
        if math.isfinite(v):
            max_v_spread = max(max_v_spread, v)
        if math.isfinite(a):
            max_a_spread = max(max_a_spread, a)
    ok = max(max_v_spread, max_a_spread) <= GEOMETRY_RELATIVE_SPREAD_TOLERANCE
    return ok, max_v_spread, max_a_spread


def inspect_isca_file(path: str | Path, *, ice_habit: str, surface_roughness: str) -> tuple[SourceFileRecord, pd.DataFrame | None]:
    p = Path(path)
    if not p.exists():
        return SourceFileRecord(
            ice_habit=ice_habit,
            surface_roughness=surface_roughness,
            path=str(p),
            exists=False,
            status="MISSING_SOURCE_FILE",
            detail="Expected TAMU V2 isca.dat not found.",
        ), None
    try:
        raw = read_tamu_isca_dat(p)
    except Exception as exc:
        return SourceFileRecord(
            ice_habit=ice_habit,
            surface_roughness=surface_roughness,
            path=str(p),
            exists=True,
            status="SOURCE_PARSE_ERROR",
            detail=f"{type(exc).__name__}: {exc}",
        ), None

    required = {
        "wavelength_um", "maximum_dimension_um", "volume_um3", "projected_area_um2",
        "extinction_efficiency", "single_scattering_albedo", "asymmetry_parameter",
    }
    if not required.issubset(raw.columns):
        return SourceFileRecord(
            ice_habit=ice_habit,
            surface_roughness=surface_roughness,
            path=str(p),
            exists=True,
            row_count=len(raw),
            status="SOURCE_SCHEMA_INVALID",
            detail=f"Missing columns: {sorted(required-set(raw.columns))}",
        ), raw

    for c in required:
        raw[c] = pd.to_numeric(raw[c], errors="coerce")
    row_count = int(len(raw))
    wavelengths = pd.to_numeric(raw["wavelength_um"], errors="coerce").dropna()
    sizes = pd.to_numeric(raw["maximum_dimension_um"], errors="coerce").dropna()
    geometry_ok, v_spread, a_spread = _geometry_consistency(raw.dropna(subset=["maximum_dimension_um"]))

    reasons: list[str] = []
    if row_count != SOURCE_EXPECTED_ISCA_ROWS:
        reasons.append(f"row_count={row_count}, expected={SOURCE_EXPECTED_ISCA_ROWS}")
    if wavelengths.nunique() != SOURCE_EXPECTED_WAVELENGTH_COUNT:
        reasons.append(f"wavelength_count={wavelengths.nunique()}, expected={SOURCE_EXPECTED_WAVELENGTH_COUNT}")
    if sizes.nunique() != SOURCE_EXPECTED_SIZE_COUNT:
        reasons.append(f"particle_size_count={sizes.nunique()}, expected={SOURCE_EXPECTED_SIZE_COUNT}")
    if len(wavelengths):
        if not math.isclose(float(wavelengths.min()), SOURCE_SHORTWAVE_RANGE_UM[0], rel_tol=0.0, abs_tol=1e-9):
            reasons.append(f"min_wavelength_um={float(wavelengths.min())}, expected={SOURCE_SHORTWAVE_RANGE_UM[0]}")
        if not math.isclose(float(wavelengths.max()), SOURCE_SHORTWAVE_RANGE_UM[1], rel_tol=0.0, abs_tol=1e-9):
            reasons.append(f"max_wavelength_um={float(wavelengths.max())}, expected={SOURCE_SHORTWAVE_RANGE_UM[1]}")
    if len(sizes):
        if not math.isclose(float(sizes.min()), SOURCE_PARTICLE_SIZE_RANGE_UM[0], rel_tol=0.0, abs_tol=1e-9):
            reasons.append(f"min_maximum_dimension_um={float(sizes.min())}, expected={SOURCE_PARTICLE_SIZE_RANGE_UM[0]}")
        if not math.isclose(float(sizes.max()), SOURCE_PARTICLE_SIZE_RANGE_UM[1], rel_tol=0.0, abs_tol=1e-9):
            reasons.append(f"max_maximum_dimension_um={float(sizes.max())}, expected={SOURCE_PARTICLE_SIZE_RANGE_UM[1]}")
    if not geometry_ok:
        reasons.append(f"geometry varies across wavelength: volume spread={v_spread:.3g}, area spread={a_spread:.3g}")

    finite_optics = raw[["extinction_efficiency", "single_scattering_albedo", "asymmetry_parameter"]].replace([np.inf, -np.inf], np.nan)
    if finite_optics.isna().any().any():
        reasons.append("nonnumeric/missing Qext/SSA/g values")
    if (raw["extinction_efficiency"] < 0).fillna(False).any():
        reasons.append("negative extinction efficiency")
    if (~raw["single_scattering_albedo"].between(0.0, 1.0)).fillna(True).any():
        reasons.append("SSA outside [0,1]")
    if (~raw["asymmetry_parameter"].between(-1.0, 1.0)).fillna(True).any():
        reasons.append("asymmetry factor outside [-1,1]")
    if (raw["volume_um3"] <= 0).fillna(True).any() or (raw["projected_area_um2"] <= 0).fillna(True).any():
        reasons.append("nonpositive volume/projected area")

    record = SourceFileRecord(
        ice_habit=ice_habit,
        surface_roughness=surface_roughness,
        path=str(p),
        exists=True,
        row_count=row_count,
        wavelength_count=int(wavelengths.nunique()),
        particle_size_count=int(sizes.nunique()),
        min_wavelength_um=float(wavelengths.min()) if len(wavelengths) else None,
        max_wavelength_um=float(wavelengths.max()) if len(wavelengths) else None,
        min_maximum_dimension_um=float(sizes.min()) if len(sizes) else None,
        max_maximum_dimension_um=float(sizes.max()) if len(sizes) else None,
        geometry_consistent=geometry_ok,
        source_sha256=_sha256_file(p),
        status="PASS" if not reasons else "FAIL",
        detail="; ".join(reasons),
    )
    return record, raw


def spectral_grid_audit(raw: pd.DataFrame, *, ice_habit: str, surface_roughness: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if raw is None or raw.empty:
        for wl in ICE_OPTICS_WAVELENGTHS_NM:
            rows.append({
                "ice_habit": ice_habit,
                "surface_roughness": surface_roughness,
                "target_wavelength_nm": wl,
                "target_wavelength_um": wl / 1000.0,
                "source_low_um": np.nan,
                "source_high_um": np.nan,
                "source_span_nm": np.nan,
                "selection_mode": "SOURCE_UNAVAILABLE",
                "status": "FAIL",
            })
        return pd.DataFrame(rows)
    x = np.array(sorted(pd.to_numeric(raw["wavelength_um"], errors="coerce").dropna().unique()), dtype=float)
    for wl in ICE_OPTICS_WAVELENGTHS_NM:
        t = wl / 1000.0
        exact = x[np.isclose(x, t, rtol=0.0, atol=1e-12)]
        if len(exact):
            low = high = float(exact[0])
            mode = "EXACT_SOURCE_WAVELENGTH"
            status = "PASS"
        else:
            hi_i = int(np.searchsorted(x, t, side="right"))
            lo_i = hi_i - 1
            if lo_i < 0 or hi_i >= len(x):
                low = high = float("nan")
                mode = "OUTSIDE_SOURCE_SPECTRAL_DOMAIN"
                status = "FAIL"
            else:
                low, high = float(x[lo_i]), float(x[hi_i])
                mode = "LINEAR_INTERPOLATION_WITHIN_SOURCE_GRID"
                status = "PASS"
        span_nm = (high - low) * 1000.0 if math.isfinite(low) and math.isfinite(high) else np.nan
        rows.append({
            "ice_habit": ice_habit,
            "surface_roughness": surface_roughness,
            "target_wavelength_nm": int(wl),
            "target_wavelength_um": t,
            "source_low_um": low,
            "source_high_um": high,
            "source_span_nm": span_nm,
            "selection_mode": mode,
            "status": status,
        })
    return pd.DataFrame(rows)


def discover_and_inspect_source(root: str | Path) -> tuple[pd.DataFrame, dict[tuple[str, str], pd.DataFrame], pd.DataFrame]:
    records: list[dict[str, Any]] = []
    raws: dict[tuple[str, str], pd.DataFrame] = {}
    spectral_parts: list[pd.DataFrame] = []
    for habit in HABITS:
        for rough in ROUGHNESS_STATES:
            p = resolve_isca_path(root, habit, rough)
            rec, raw = inspect_isca_file(p, ice_habit=habit, surface_roughness=rough)
            records.append(asdict(rec))
            if raw is not None:
                raws[(habit, rough)] = raw
            spectral_parts.append(spectral_grid_audit(raw if raw is not None else pd.DataFrame(), ice_habit=habit, surface_roughness=rough))
    return pd.DataFrame(records), raws, pd.concat(spectral_parts, ignore_index=True)


def _lut_group_qa(lut: pd.DataFrame) -> dict[str, Any]:
    if lut is None or lut.empty:
        return {
            "row_count": 0,
            "expected_row_count": len(HABITS) * len(ROUGHNESS_STATES) * SOURCE_EXPECTED_SIZE_COUNT * len(ICE_OPTICS_WAVELENGTHS_NM),
            "six_band_group_count": 0,
            "duplicate_key_rows": 0,
            "nonfinite_rows": 0,
            "status": "FAIL",
            "reasons": ["LUT empty"],
        }
    expected_rows = len(HABITS) * len(ROUGHNESS_STATES) * SOURCE_EXPECTED_SIZE_COUNT * len(ICE_OPTICS_WAVELENGTHS_NM)
    key_cols = ["ice_habit", "surface_roughness", "maximum_dimension_um", "wavelength_nm"]
    dup = int(lut.duplicated(key_cols, keep=False).sum())
    numeric = [
        "wavelength_nm", "maximum_dimension_um", "effective_diameter_um", "effective_radius_um",
        "mass_extinction_coefficient_m2_kg", "single_scattering_albedo", "asymmetry_parameter",
    ]
    finite = lut[numeric].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
    nonfinite = int(finite.isna().any(axis=1).sum())
    group_counts = lut.groupby(["ice_habit", "surface_roughness", "maximum_dimension_um"])["wavelength_nm"].nunique()
    six_band_groups = int((group_counts == len(ICE_OPTICS_WAVELENGTHS_NM)).sum())
    expected_groups = len(HABITS) * len(ROUGHNESS_STATES) * SOURCE_EXPECTED_SIZE_COUNT

    # Detect ambiguity in the runtime r_eff coordinate.  The portable evaluator
    # keys by effective radius within each habit/roughness group, so duplicate
    # radius values mapped to different Dmax would be ambiguous and must be
    # resolved scientifically before release.
    radius_table = lut[["ice_habit", "surface_roughness", "maximum_dimension_um", "effective_radius_um"]].drop_duplicates()
    radius_dups = radius_table.duplicated(["ice_habit", "surface_roughness", "effective_radius_um"], keep=False)
    ambiguous_radius_rows = int(radius_dups.sum())

    reasons: list[str] = []
    if len(lut) != expected_rows:
        reasons.append(f"row_count={len(lut)}, expected={expected_rows}")
    if six_band_groups != expected_groups:
        reasons.append(f"six_band_groups={six_band_groups}, expected={expected_groups}")
    if dup:
        reasons.append(f"duplicate source-size-band keys={dup}")
    if nonfinite:
        reasons.append(f"nonfinite optical rows={nonfinite}")
    if ambiguous_radius_rows:
        reasons.append(f"ambiguous effective-radius coordinate rows={ambiguous_radius_rows}")
    if (lut["mass_extinction_coefficient_m2_kg"] < 0).any():
        reasons.append("negative k_ext")
    if (~lut["single_scattering_albedo"].between(0.0, 1.0)).any():
        reasons.append("SSA outside [0,1]")
    if (~lut["asymmetry_parameter"].between(-1.0, 1.0)).any():
        reasons.append("g outside [-1,1]")

    return {
        "row_count": int(len(lut)),
        "expected_row_count": int(expected_rows),
        "six_band_group_count": six_band_groups,
        "expected_six_band_group_count": expected_groups,
        "duplicate_key_rows": dup,
        "nonfinite_rows": nonfinite,
        "ambiguous_effective_radius_rows": ambiguous_radius_rows,
        "k_ext_min_m2_kg": float(lut["mass_extinction_coefficient_m2_kg"].min()),
        "k_ext_max_m2_kg": float(lut["mass_extinction_coefficient_m2_kg"].max()),
        "ssa_min": float(lut["single_scattering_albedo"].min()),
        "ssa_max": float(lut["single_scattering_albedo"].max()),
        "g_min": float(lut["asymmetry_parameter"].min()),
        "g_max": float(lut["asymmetry_parameter"].max()),
        "status": "PASS" if not reasons else "FAIL",
        "reasons": reasons,
    }


def build_authoritative_six_band_lut(
    source_root: str | Path,
    *,
    strict_source: bool = True,
    source_archive_md5_verified: bool = False,
) -> AuthoritativeBuildResult:
    inventory, raws, spectral = discover_and_inspect_source(source_root)
    source_failures = inventory[inventory["status"].astype(str) != "PASS"]
    spectral_failures = spectral[spectral["status"].astype(str) != "PASS"]

    lut_parts: list[pd.DataFrame] = []
    if source_failures.empty and spectral_failures.empty:
        for habit in HABITS:
            for rough in ROUGHNESS_STATES:
                raw = raws[(habit, rough)]
                lut_parts.append(normalize_tamu_isca_frame(
                    raw,
                    ice_habit=habit,
                    surface_roughness=rough,
                    source_dataset=SOURCE_DATASET,
                    source_version=SOURCE_VERSION,
                ))
    elif not strict_source:
        for (habit, rough), raw in raws.items():
            try:
                part = normalize_tamu_isca_frame(
                    raw,
                    ice_habit=habit,
                    surface_roughness=rough,
                    source_dataset=SOURCE_DATASET,
                    source_version=SOURCE_VERSION,
                )
                if not part.empty:
                    lut_parts.append(part)
            except Exception:
                pass

    if lut_parts:
        lut = pd.concat(lut_parts, ignore_index=True)
        try:
            lut = validate_ice_optics_lut(lut, require_full_six_band=True)
        except Exception:
            # Keep the rows for QA reporting; release gate below remains FAIL.
            lut = pd.concat(lut_parts, ignore_index=True)
    else:
        lut = pd.DataFrame(columns=LUT_REQUIRED_COLUMNS)

    lut_qa = _lut_group_qa(lut)
    reasons: list[str] = []
    if not source_failures.empty:
        reasons.append(f"source_file_failures={len(source_failures)}")
    if not spectral_failures.empty:
        reasons.append(f"spectral_grid_failures={len(spectral_failures)}")
    if lut_qa["status"] != "PASS":
        reasons.extend([f"lut:{x}" for x in lut_qa.get("reasons", [])])
    source_qa_pass = not reasons
    release_reasons = list(reasons)
    if not source_archive_md5_verified:
        release_reasons.append("published_source_archive_md5_not_verified")

    qa = {
        "build_gate_version": AUTHORITATIVE_BUILD_GATE_VERSION,
        "source_contract_version": AUTHORITATIVE_SOURCE_CONTRACT_VERSION,
        "source_dataset": SOURCE_DATASET,
        "source_version": SOURCE_VERSION,
        "source_root": str(Path(source_root).expanduser()),
        "strict_source": bool(strict_source),
        "published_source_archive_md5_verified": bool(source_archive_md5_verified),
        "expected_source_file_count": len(HABITS) * len(ROUGHNESS_STATES),
        "source_file_pass_count": int((inventory["status"].astype(str) == "PASS").sum()) if len(inventory) else 0,
        "source_file_fail_count": int((inventory["status"].astype(str) != "PASS").sum()) if len(inventory) else len(HABITS) * len(ROUGHNESS_STATES),
        "spectral_target_pass_count": int((spectral["status"].astype(str) == "PASS").sum()) if len(spectral) else 0,
        "spectral_target_fail_count": int((spectral["status"].astype(str) != "PASS").sum()) if len(spectral) else len(HABITS) * len(ROUGHNESS_STATES) * len(ICE_OPTICS_WAVELENGTHS_NM),
        "lut_qa": lut_qa,
        "source_qa_status": "PASS" if source_qa_pass else "FAIL",
        "overall_status": "PASS" if not release_reasons else "FAIL",
        "release_ready": not release_reasons,
        "reasons": release_reasons,
        "physics_promotion_allowed": False,
        "note": "PASS certifies source-to-portable-LUT construction only; it does not promote ice optics into Formation/Viewing/Glow production physics.",
    }
    return AuthoritativeBuildResult(lut=lut, source_inventory=inventory, spectral_grid_audit=spectral, qa_summary=qa)


def write_authoritative_build_outputs(
    result: AuthoritativeBuildResult,
    output_dir: str | Path,
    *,
    include_lut_when_failed: bool = False,
) -> dict[str, str]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}

    inv = out / "ice_optics_source_inventory_v1.csv"
    result.source_inventory.to_csv(inv, index=False)
    paths[inv.name] = str(inv)

    spec = out / "ice_optics_spectral_grid_audit_v1.csv"
    result.spectral_grid_audit.to_csv(spec, index=False)
    paths[spec.name] = str(spec)

    qa = out / "ice_optics_authoritative_build_qa_v1.json"
    qa.write_text(json.dumps(result.qa_summary, ensure_ascii=False, indent=2), encoding="utf-8")
    paths[qa.name] = str(qa)

    source = out / "ice_optics_authoritative_source_manifest_v1.json"
    source.write_text(json.dumps(authoritative_source_manifest(), ensure_ascii=False, indent=2), encoding="utf-8")
    paths[source.name] = str(source)

    if result.ready or include_lut_when_failed:
        lut_path = out / "ice_optics_lut_v1.csv"
        result.lut.to_csv(lut_path, index=False)
        paths[lut_path.name] = str(lut_path)

    manifest_payload = {
        "contract": "FIRECLOUD_ICE_OPTICS_AUTHORITATIVE_BUILD_OUTPUT_V1",
        "release_ready": result.ready,
        "files": {},
    }
    for name, p in paths.items():
        pp = Path(p)
        manifest_payload["files"][name] = {
            "sha256": _sha256_file(pp),
            "byte_size": pp.stat().st_size,
        }
    manifest = out / "manifest.json"
    manifest.write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    paths[manifest.name] = str(manifest)
    return paths
