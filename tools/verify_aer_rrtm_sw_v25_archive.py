#!/usr/bin/env python3
"""Inspect or acquire the historical AER RRTM_SW v2.5 source archive.

This is provenance tooling only.  It records observed local bytes, hashes and a
non-extracting tar manifest.  It MUST NOT by itself upgrade PhysicsCore's
qualified evidence to original-tarball byte identity; that promotion requires
review of the acquired bytes and provenance chain.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tarfile
import urllib.request
from typing import Any

OFFICIAL_URL = "https://files.aer.com/rtweb/aer_rrtm_sw/aer_rrtm_sw_v2.5.tar.gz"
EXPECTED_SUFFIXES = (
    "src/cldprop.f",
    "src/taumoldis.f",
    "makefiles/make_rrtm_sw_linux_pgi",
    "rrtm_sw_instructions",
    "update_rrtm_sw_v2.5.txt",
)


def _hashes(path: Path) -> tuple[str, str, int]:
    h256 = hashlib.sha256()
    h5 = hashlib.md5(usedforsecurity=False)
    total = 0
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            h256.update(chunk)
            h5.update(chunk)
    return h256.hexdigest(), h5.hexdigest(), total


def inspect_archive(path: str | Path, *, source_url: str | None = None) -> dict[str, Any]:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(p)
    sha256, md5, size = _hashes(p)
    with tarfile.open(p, mode="r:gz") as tf:
        members = [m.name for m in tf.getmembers() if m.isfile()]
    suffix_hits = {
        suffix: [name for name in members if name == suffix or name.endswith("/" + suffix)]
        for suffix in EXPECTED_SUFFIXES
    }
    complete = all(len(v) == 1 for v in suffix_hits.values())
    return {
        "schema": "twfc.aer-rrtm-sw-v25-archive-observation.v1",
        "archive_path": str(p),
        "source_url": source_url,
        "archive_bytes_observed": True,
        "sha256": sha256,
        "md5": md5,
        "byte_size": size,
        "file_member_count": len(members),
        "member_names": members,
        "expected_suffix_hits": suffix_hits,
        "expected_footprint_complete": complete,
        "provenance_qualified_original_archive_hash": False,
        "original_tarball_byte_identity_proven": False,
        "qualification_note": (
            "Observed local archive bytes and hashes only. Review provenance and compare "
            "against the qualified historical source tree before changing PhysicsCore gates."
        ),
    }


def download_official(destination: str | Path, *, timeout: int = 120) -> Path:
    dest = Path(destination)
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(
        OFFICIAL_URL,
        headers={"User-Agent": "Taiwan-Firecloud-PhysicsCore-Provenance/1.0"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp, dest.open("wb") as out:
        while True:
            chunk = resp.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
    return dest


def main() -> int:
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--archive", help="Inspect an already acquired local tar.gz")
    src.add_argument("--download-to", help="Download the pinned official AER URL, then inspect")
    ap.add_argument("--json-out", help="Optional report JSON path")
    ap.add_argument("--timeout", type=int, default=120)
    args = ap.parse_args()

    if args.download_to:
        path = download_official(args.download_to, timeout=args.timeout)
        source_url = OFFICIAL_URL
    else:
        path = Path(args.archive)
        source_url = None

    report = inspect_archive(path, source_url=source_url)
    data = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    if args.json_out:
        Path(args.json_out).write_text(data + "\n", encoding="utf-8")
    print(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
