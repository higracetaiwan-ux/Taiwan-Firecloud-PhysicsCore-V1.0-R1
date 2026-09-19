#!/usr/bin/env python3
"""Compare AER RRTM_SW v2.5 scientific-source trees conservatively.

This provenance helper compares the 26 Fortran source files observed in the
pinned AER 2004 release tree. It collapses expanded CVS keywords before
comparison and recognizes only two explicitly documented operational deltas:

* ``src/rrtatm.f``: three date/time-output calls commented out.
* ``src/rrtm.f``: one input filename literal changed from ``INPUT_RRTM`` to
  ``input_rrtm_MLS``.

The tool may qualify *scientific-source semantic equivalence* for the compared
source set. It never proves whole-repository equality, original tarball byte
identity, historical archive hash, or recovery of the Fu96 pre-averaging
generator.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

SCIENTIFIC_SOURCE_PATHS = (
    "src/ErrPack.f",
    "src/LINPAK.f",
    "src/RDI1MACH.f",
    "src/cldprop.f",
    "src/disort.f",
    "src/extra.f",
    "src/k_g.f",
    "src/k_gB16.f",
    "src/k_gB17.f",
    "src/k_gB18.f",
    "src/k_gB19.f",
    "src/k_gB20.f",
    "src/k_gB21.f",
    "src/k_gB22.f",
    "src/k_gB23.f",
    "src/k_gB24.f",
    "src/k_gB25.f",
    "src/k_gB27.f",
    "src/k_gB28.f",
    "src/k_gB29.f",
    "src/param.f",
    "src/rrtatm.f",
    "src/rrtm.f",
    "src/rtrdis.f",
    "src/setcoef.f",
    "src/taumoldis.f",
)

_CVS_EXPANDED = re.compile(r"\$([A-Za-z][A-Za-z0-9_]*):[^$]*\$")


def normalize_cvs_keywords(text: str) -> str:
    """Collapse expanded CVS keywords and normalize line endings."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return _CVS_EXPANDED.sub(lambda m: f"${m.group(1)}$", text)


def _line_differences(a: str, b: str) -> list[dict[str, Any]]:
    aa, bb = a.split("\n"), b.split("\n")
    out: list[dict[str, Any]] = []
    for i in range(max(len(aa), len(bb))):
        av = aa[i] if i < len(aa) else None
        bv = bb[i] if i < len(bb) else None
        if av != bv:
            out.append({"line": i + 1, "official": av, "mirror": bv})
    return out


def _rrtatm_allowed(diffs: list[dict[str, Any]]) -> bool:
    if len(diffs) != 3:
        return False
    needles = ("CALL LBLDAT(HDATE)", "CALL FTIME (HTIME)", "WRITE (IPR,900) HDATE,HTIME")
    for d, needle in zip(diffs, needles):
        a = (d["official"] or "").lstrip()
        b = (d["mirror"] or "").lstrip()
        if needle not in a:
            return False
        if not b.startswith("!") or needle not in b:
            return False
    return True


def _rrtm_allowed(diffs: list[dict[str, Any]]) -> bool:
    if len(diffs) != 1:
        return False
    a = diffs[0]["official"] or ""
    b = diffs[0]["mirror"] or ""
    return (
        "OPEN (IRD,FILE='INPUT_RRTM',FORM='FORMATTED')" in a
        and "OPEN (IRD,FILE='input_rrtm_MLS',FORM='FORMATTED')" in b
    )


def compare_text_pair(path: str, official_text: str, mirror_text: str) -> dict[str, Any]:
    a = normalize_cvs_keywords(official_text)
    b = normalize_cvs_keywords(mirror_text)
    if a == b:
        return {
            "path": path,
            "classification": "CVS_NORMALIZED_FULL_FILE_MATCH",
            "scientific_semantics_equivalent": True,
            "raw_byte_identity_proven": False,
            "delta_line_count": 0,
            "deltas": [],
        }
    diffs = _line_differences(a, b)
    allowed = False
    cls = "UNEXPECTED_DELTA"
    if path == "src/rrtatm.f" and _rrtatm_allowed(diffs):
        allowed = True
        cls = "ALLOWED_OPERATIONAL_DELTA_DATE_TIME_OUTPUT_ONLY"
    elif path == "src/rrtm.f" and _rrtm_allowed(diffs):
        allowed = True
        cls = "ALLOWED_OPERATIONAL_DELTA_INPUT_FILENAME_ONLY"
    return {
        "path": path,
        "classification": cls,
        "scientific_semantics_equivalent": allowed,
        "raw_byte_identity_proven": False,
        "delta_line_count": len(diffs),
        "deltas": diffs,
    }


def compare_trees(official_root: str | Path, mirror_root: str | Path) -> dict[str, Any]:
    official_root = Path(official_root)
    mirror_root = Path(mirror_root)
    results: list[dict[str, Any]] = []
    missing: list[str] = []
    for rel in SCIENTIFIC_SOURCE_PATHS:
        op = official_root / rel
        mp = mirror_root / rel
        if not op.is_file() or not mp.is_file():
            missing.append(rel)
            results.append({
                "path": rel,
                "classification": "MISSING",
                "scientific_semantics_equivalent": False,
                "raw_byte_identity_proven": False,
                "delta_line_count": None,
                "deltas": [],
            })
            continue
        results.append(compare_text_pair(rel, op.read_text(encoding="utf-8"), mp.read_text(encoding="utf-8")))

    full_matches = sum(r["classification"] == "CVS_NORMALIZED_FULL_FILE_MATCH" for r in results)
    operational = sum(r["classification"].startswith("ALLOWED_OPERATIONAL_DELTA_") for r in results)
    unexpected = [r["path"] for r in results if r["classification"] == "UNEXPECTED_DELTA"]
    delta_lines = sum(r["delta_line_count"] or 0 for r in results if r["classification"].startswith("ALLOWED_OPERATIONAL_DELTA_"))
    semantic_ok = not missing and not unexpected and all(r["scientific_semantics_equivalent"] for r in results)
    return {
        "schema": "twfc.rrtm-sw-v25-scientific-source-semantic-equivalence.v1",
        "scientific_source_file_count": len(SCIENTIFIC_SOURCE_PATHS),
        "cvs_normalized_full_file_match_count": full_matches,
        "allowed_operational_delta_file_count": operational,
        "allowed_operational_delta_line_count": delta_lines,
        "missing_files": missing,
        "unexpected_delta_files": unexpected,
        "scientific_source_semantic_equivalence_qualified": semantic_ok,
        "whole_repository_equality_proven": False,
        "original_tarball_byte_identity_proven": False,
        "historical_archive_hash_recovered": False,
        "preaveraging_generator_recovered": False,
        "files": results,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("official_root")
    ap.add_argument("mirror_root")
    ap.add_argument("--json-out")
    args = ap.parse_args()
    report = compare_trees(args.official_root, args.mirror_root)
    data = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    if args.json_out:
        Path(args.json_out).write_text(data + "\n", encoding="utf-8")
    print(data)
    return 0 if report["scientific_source_semantic_equivalence_qualified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
