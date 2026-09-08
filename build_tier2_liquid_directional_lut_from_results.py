from __future__ import annotations

import argparse
import json
from pathlib import Path
import pandas as pd

from firecloud.tier2_directional_scattering_runtime import (
    LUT_FILENAME,
    MANIFEST_FILENAME,
    validate_directional_lut_bytes,
)
from firecloud.tier2_liquid_directional_calibration_pipeline import (
    build_production_lut_from_external_results,
)


def main() -> int:
    p = argparse.ArgumentParser(description="以通過 QC 的外部 genuine RT 結果建立 R5.7.23 production directional LUT package。")
    p.add_argument("--jobs-csv", required=True)
    p.add_argument("--results-csv", required=True)
    p.add_argument("--metadata-json", required=True)
    p.add_argument("--domain-spec-json", required=True, help="生成 jobs 時使用的 exact domain spec，用於 SHA256 provenance")
    p.add_argument("--output-dir", required=True)
    p.add_argument("--max-mc-relative-sigma", type=float, default=0.02)
    p.add_argument("--max-mc-absolute-sigma", type=float, default=0.01)
    p.add_argument("--minimum-photon-count", type=int, default=1)
    args = p.parse_args()

    jobs = pd.read_csv(args.jobs_csv)
    results = pd.read_csv(args.results_csv)
    metadata = json.loads(Path(args.metadata_json).read_text(encoding="utf-8"))
    domain_spec = json.loads(Path(args.domain_spec_json).read_text(encoding="utf-8"))
    csv_bytes, manifest_bytes, audit = build_production_lut_from_external_results(
        jobs=jobs,
        results=results,
        metadata=metadata,
        max_mc_relative_sigma=args.max_mc_relative_sigma,
        max_mc_absolute_sigma=args.max_mc_absolute_sigma,
        minimum_photon_count=args.minimum_photon_count,
        domain_spec=domain_spec,
    )
    validation = validate_directional_lut_bytes(csv_bytes, manifest_bytes)
    if not validation.get("ok", False):
        raise RuntimeError("RUNTIME_PACKAGE_VALIDATION_FAILED:" + json.dumps(validation, ensure_ascii=False))

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / LUT_FILENAME).write_bytes(csv_bytes)
    (out / MANIFEST_FILENAME).write_bytes(manifest_bytes)
    build_audit = {**audit, "runtime_validation": validation, "installed_into_runtime": False}
    (out / "tier2_directional_scattering_lut_build_audit.json").write_text(
        json.dumps(build_audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(build_audit, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
