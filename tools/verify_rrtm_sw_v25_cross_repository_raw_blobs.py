#!/usr/bin/env python3
"""Deterministic Step 3Q.14 cross-repository Git-blob manifest verifier.

This tool compares two *already exported* Git tree manifests. It performs no
network access and deliberately does not infer original AER tarball identity.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

SCIENTIFIC_SOURCE_FILENAMES = (
    "ErrPack.f", "LINPAK.f", "RDI1MACH.f", "cldprop.f", "disort.f", "extra.f",
    "k_g.f", "k_gB16.f", "k_gB17.f", "k_gB18.f", "k_gB19.f", "k_gB20.f",
    "k_gB21.f", "k_gB22.f", "k_gB23.f", "k_gB24.f", "k_gB25.f", "k_gB27.f",
    "k_gB28.f", "k_gB29.f", "param.f", "rrtatm.f", "rrtm.f", "rtrdis.f",
    "setcoef.f", "taumoldis.f",
)
CRITICAL_FILENAMES = ("cldprop.f", "taumoldis.f", "k_gB24.f", "k_gB25.f")


def _load_tree(path: Path) -> list[dict[str, Any]]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(obj, dict) and isinstance(obj.get("tree"), list):
        return list(obj["tree"])
    if isinstance(obj, list):
        return list(obj)
    raise ValueError("manifest must be a Git tree JSON object with a tree[] list, or a tree-entry list")


def _manifest_map(entries: Iterable[dict[str, Any]], prefix: str) -> dict[str, str]:
    out: dict[str, str] = {}
    prefix = prefix.rstrip("/") + "/" if prefix else ""
    for row in entries:
        if str(row.get("type", "blob")) != "blob":
            continue
        path = str(row.get("path", ""))
        sha = str(row.get("sha", ""))
        if not sha or (prefix and not path.startswith(prefix)):
            continue
        rel = path[len(prefix):] if prefix else path
        out[rel] = sha
    return out


def compare_tree_manifests(
    left_entries: Iterable[dict[str, Any]],
    right_entries: Iterable[dict[str, Any]],
    *,
    left_prefix: str = "sw",
    right_prefix: str = "SW/src",
) -> dict[str, Any]:
    left = _manifest_map(left_entries, left_prefix)
    right = _manifest_map(right_entries, right_prefix)
    rows = []
    for name in SCIENTIFIC_SOURCE_FILENAMES:
        lsha = left.get(name)
        rsha = right.get(name)
        rows.append({
            "file": name,
            "left_sha": lsha,
            "right_sha": rsha,
            "present_both": bool(lsha and rsha),
            "raw_blob_equal": bool(lsha and rsha and lsha == rsha),
            "critical": name in CRITICAL_FILENAMES,
        })
    matched = [r for r in rows if r["raw_blob_equal"]]
    unmatched = [r for r in rows if not r["raw_blob_equal"]]
    critical = [r for r in rows if r["critical"]]
    return {
        "scientific_source_file_count": len(SCIENTIFIC_SOURCE_FILENAMES),
        "raw_blob_match_count": len(matched),
        "raw_blob_nonmatch_count": len(unmatched),
        "raw_blob_nonmatch_files": [r["file"] for r in unmatched],
        "critical_file_count": len(CRITICAL_FILENAMES),
        "critical_raw_blob_match_count": sum(1 for r in critical if r["raw_blob_equal"]),
        "critical_raw_blob_replication_qualified": all(r["raw_blob_equal"] for r in critical),
        "original_aer_tarball_byte_identity_proven": False,
        "authoritative_original_archive_hash_recovered": False,
        "rows": rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("left_manifest", type=Path)
    ap.add_argument("right_manifest", type=Path)
    ap.add_argument("--left-prefix", default="sw")
    ap.add_argument("--right-prefix", default="SW/src")
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    result = compare_tree_manifests(
        _load_tree(args.left_manifest),
        _load_tree(args.right_manifest),
        left_prefix=args.left_prefix,
        right_prefix=args.right_prefix,
    )
    data = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(data, encoding="utf-8")
    else:
        print(data, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
