from __future__ import annotations

import argparse
import json
from pathlib import Path
import pandas as pd

from firecloud.tier2_liquid_directional_calibration_pipeline import (
    build_libradtran_mystic_solver_recipe,
    plan_liquid_directional_calibration_domain,
    select_liquid_calibration_targets,
    write_external_calibration_bundle,
)


def main() -> int:
    p = argparse.ArgumentParser(description="建立 R5.7.23 genuine liquid-cloud full-directional 外部 RT 校準工作包。")
    p.add_argument("--foundation-csv", required=True, help="Tier-2 directional foundation CSV")
    p.add_argument("--readiness-csv", required=True, help="Tier-2 readiness / target optical truth CSV")
    p.add_argument("--output-dir", required=True)
    p.add_argument("--libradtran-version", default="UNRESOLVED_EXTERNAL_RUNTIME")
    p.add_argument("--photons-per-job", type=int, default=1_000_000)
    p.add_argument("--angular-margin-deg", type=float, default=2.0)
    p.add_argument("--relative-azimuth-margin-deg", type=float, default=5.0)
    p.add_argument("--angular-step-deg", type=float, default=2.0)
    p.add_argument("--relative-azimuth-step-deg", type=float, default=2.5)
    args = p.parse_args()

    foundation = pd.read_csv(args.foundation_csv)
    readiness = pd.read_csv(args.readiness_csv)
    targets = select_liquid_calibration_targets(foundation=foundation, readiness=readiness)
    domain = plan_liquid_directional_calibration_domain(
        foundation=foundation,
        readiness=readiness,
        angular_margin_deg=args.angular_margin_deg,
        relative_azimuth_margin_deg=args.relative_azimuth_margin_deg,
        angular_step_deg=args.angular_step_deg,
        relative_azimuth_step_deg=args.relative_azimuth_step_deg,
    )
    recipe = build_libradtran_mystic_solver_recipe(
        libRadtran_version=args.libradtran_version,
        photons_per_job=args.photons_per_job,
    )
    out = Path(args.output_dir)
    audit = write_external_calibration_bundle(out, domain_spec=domain, solver_recipe=recipe)
    targets.to_csv(out / "tier2_real_liquid_calibration_targets.csv", index=False)
    print(json.dumps({
        **audit,
        "real_target_count": int(len(targets)),
        "observed_domain": domain.get("observed_domain", {}),
        "production_lut_state": "NOT_YET_GENERATED_EXTERNAL_RT_REQUIRED",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
