#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from firecloud.ice_optics_authoritative import (
    build_authoritative_six_band_lut,
    write_authoritative_build_outputs,
    verify_shortwave_archive_md5,
)
from firecloud.ice_optics_portable import build_portable_package_zip_bytes


def main() -> int:
    p = argparse.ArgumentParser(
        description="Build and QA the authoritative Firecloud six-band Ice Optics LUT from a local Yang/Bi V2 Data_0.2_15.25 extraction."
    )
    p.add_argument("--source-root", required=True, help="Directory containing Data_0.2_15.25/ or its habit folders")
    p.add_argument("--output-dir", required=True, help="Directory for source inventory, spectral audit, QA and LUT")
    p.add_argument("--archive", help="Optional original Data_0.2_15.25.tar.gz; verifies published MD5 before building")
    p.add_argument("--non-strict", action="store_true", help="Diagnostic only: build any available groups; release_ready will remain false if source is incomplete")
    p.add_argument("--emit-failed-lut", action="store_true", help="Diagnostic only: write partial LUT even when QA fails")
    p.add_argument("--portable-zip", help="If QA passes, also write standalone WINDY portable package ZIP here")
    p.add_argument("--physicscore-version", default="1.0.0-R5.7.41.3.4.10.12")
    p.add_argument("--science-baseline", default="R5.7.41.2_SHADOW_COT_AB_FROZEN")
    args = p.parse_args()

    archive_verified = False
    if args.archive:
        archive_audit = verify_shortwave_archive_md5(args.archive)
        print(json.dumps({"archive_audit": archive_audit}, ensure_ascii=False))
        if archive_audit["status"] != "PASS":
            print("ERROR: published archive MD5 verification failed; refusing authoritative build.", file=sys.stderr)
            return 3
        archive_verified = True

    result = build_authoritative_six_band_lut(
        args.source_root,
        strict_source=not args.non_strict,
        source_archive_md5_verified=archive_verified,
    )
    paths = write_authoritative_build_outputs(result, args.output_dir, include_lut_when_failed=args.emit_failed_lut)
    print(json.dumps({"qa": result.qa_summary, "outputs": paths}, ensure_ascii=False, indent=2))

    if not result.ready:
        print("NOT READY: no calibrated portable package emitted because authoritative source QA did not pass.", file=sys.stderr)
        return 2

    if args.portable_zip:
        source_manifest = json.loads(Path(paths["ice_optics_authoritative_source_manifest_v1.json"]).read_text(encoding="utf-8"))
        payload = build_portable_package_zip_bytes(
            result.lut,
            physicscore_version=args.physicscore_version,
            science_baseline=args.science_baseline,
            source_manifest=source_manifest,
        )
        out = Path(args.portable_zip)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(payload)
        print(f"portable package: {out} ({len(payload)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
