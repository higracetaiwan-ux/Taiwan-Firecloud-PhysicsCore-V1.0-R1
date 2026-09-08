from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile
import zipfile
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from firecloud.tier2_liquid_directional_calibration_pipeline import (
    plan_liquid_directional_calibration_domain,
    select_liquid_calibration_targets,
    canonical_domain_spec_sha256,
)
from firecloud.contracts import SIX_BAND_WAVELENGTHS_NM


def _case_root(source: Path, temp: Path) -> Path:
    if source.is_dir():
        return source
    if source.suffix.lower() != ".zip":
        raise ValueError("CASE_SOURCE_MUST_BE_DIRECTORY_OR_ZIP")
    with zipfile.ZipFile(source) as zf:
        zf.extractall(temp)
    # CASE ZIPs can contain files at root or under one wrapper directory.
    matches = list(temp.rglob("v1_tier2_scattering_foundation.csv"))
    if not matches:
        raise FileNotFoundError("CASE_MISSING_V1_TIER2_SCATTERING_FOUNDATION")
    return matches[0].parent


def _positive_incident_audit(root: Path, targets: pd.DataFrame) -> dict:
    p = root / "v1_cloud_base_illumination_550_750nm.csv"
    if not p.exists() or targets.empty:
        return {"illumination_file_present": p.exists(), "positive_incident_target_count": None, "zero_incident_target_count": None, "missing_incident_target_count": None}
    illum = pd.read_csv(p)
    keys = [c for c in ("canvas_id", "solar_altitude_deg") if c in targets.columns and c in illum.columns]
    if not keys:
        return {"illumination_file_present": True, "positive_incident_target_count": None, "zero_incident_target_count": None, "missing_incident_target_count": None, "note": "NO_JOIN_KEYS"}
    q = targets[keys].drop_duplicates().merge(illum, on=keys, how="left")
    cols = []
    for wl in SIX_BAND_WAVELENGTHS_NM:
        for name in (f"relative_base_illumination_{int(wl)}nm", f"cloud_base_incident_irradiance_{int(wl)}nm", f"incident_irradiance_{int(wl)}nm"):
            if name in q.columns:
                cols.append(name); break
    if not cols:
        return {"illumination_file_present": True, "positive_incident_target_count": None, "zero_incident_target_count": None, "missing_incident_target_count": None, "note": "NO_SIX_BAND_INCIDENT_COLUMNS"}
    vals = q[cols].apply(pd.to_numeric, errors="coerce")
    any_finite = vals.notna().any(axis=1)
    positive = vals.fillna(0).gt(0).any(axis=1)
    zero = any_finite & ~positive
    return {
        "illumination_file_present": True,
        "incident_columns": cols,
        "positive_incident_target_count": int(positive.sum()),
        "zero_incident_target_count": int(zero.sum()),
        "missing_incident_target_count": int((~any_finite).sum()),
        "semantic_note": "PHYSICALLY_ZERO_INCIDENT_IS_ZERO_NOT_MISSING_AND_DOES_NOT_CREATE_NONZERO_RADIANCE",
    }


def main() -> int:
    p = argparse.ArgumentParser(description="由 PhysicsCore CASE ZIP/目錄推導 R5.7.23 liquid full-directional calibration domain。")
    p.add_argument("--case", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--angular-margin-deg", type=float, default=2.0)
    p.add_argument("--relative-azimuth-margin-deg", type=float, default=5.0)
    p.add_argument("--angular-step-deg", type=float, default=2.0)
    p.add_argument("--relative-azimuth-step-deg", type=float, default=2.5)
    args = p.parse_args()
    source = Path(args.case)
    out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="firecloud_case_domain_") as td:
        root = _case_root(source, Path(td))
        foundation = pd.read_csv(root / "v1_tier2_scattering_foundation.csv")
        readiness = pd.read_csv(root / "v1_tier2_scattering_readiness.csv")
        targets = select_liquid_calibration_targets(foundation=foundation, readiness=readiness)
        domain = plan_liquid_directional_calibration_domain(
            foundation=foundation, readiness=readiness,
            angular_margin_deg=args.angular_margin_deg,
            relative_azimuth_margin_deg=args.relative_azimuth_margin_deg,
            angular_step_deg=args.angular_step_deg,
            relative_azimuth_step_deg=args.relative_azimuth_step_deg,
        )
        audit = {
            "case_source": str(source), "case_root_name": root.name,
            "real_tier2_ready_liquid_target_count": int(len(targets)),
            "domain_spec_sha256": canonical_domain_spec_sha256(domain),
            "observed_domain": domain.get("observed_domain", {}),
            "planned_job_count": int(domain.get("planned_job_count", 0)),
            **_positive_incident_audit(root, targets),
        }
        (out / "liquid_directional_calibration_domain.json").write_text(json.dumps(domain, ensure_ascii=False, indent=2, sort_keys=True)+"\n", encoding="utf-8")
        targets.to_csv(out / "liquid_directional_case_evidence.csv", index=False)
        (out / "liquid_directional_domain_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True)+"\n", encoding="utf-8")
        print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
