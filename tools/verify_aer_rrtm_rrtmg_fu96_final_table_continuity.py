from __future__ import annotations
import re
from typing import Dict, List

TABLE_NAMES = ("EXTICE3", "SSAICE3", "ASYICE3", "FDLICE3")
BANDS = tuple(range(16, 30))
VALUES_PER_ARRAY = 46

_num_re = re.compile(r"[+-]?(?:\d+\.\d*|\.\d+|\d+)(?:[EeDd][+-]?\d+)?")


def _nums(text: str) -> List[float]:
    return [float(x.replace("D", "E").replace("d", "e")) for x in _num_re.findall(text)]


def parse_rrtm_sw_v25_tables(text: str) -> Dict[str, List[float]]:
    out: Dict[str, List[float]] = {}
    for name in TABLE_NAMES:
        for band in BANDS:
            m = re.search(rf"DATA\s*\({name}\(I,{band}\),I=1,46\)\s*/([\s\S]*?)/", text, re.I)
            if not m:
                raise ValueError(f"missing {name} band {band}")
            body = " ".join(line.lstrip().lstrip("&") for line in m.group(1).splitlines() if not line.lstrip().upper().startswith("C"))
            vals = _nums(body)
            if len(vals) != VALUES_PER_ARRAY:
                raise ValueError(f"{name} band {band}: expected 46 values, got {len(vals)}")
            out[f"{name}:{band}"] = vals
    return out


def parse_rrtmg_sw_2007_tables(text: str) -> Dict[str, List[float]]:
    out: Dict[str, List[float]] = {}
    for name in TABLE_NAMES:
        for band in BANDS:
            m = re.search(rf"{name}\s*\(:,\s*{band}\)\s*=\s*\(/\s*&?([\s\S]*?)/\)", text, re.I)
            if not m:
                raise ValueError(f"missing {name} band {band}")
            body = " ".join(line.lstrip().lstrip("&").replace("_jprb", "") for line in m.group(1).splitlines() if not line.lstrip().startswith("!"))
            vals = _nums(body)
            if len(vals) != VALUES_PER_ARRAY:
                raise ValueError(f"{name} band {band}: expected 46 values, got {len(vals)}")
            out[f"{name}:{band}"] = vals
    return out


def compare_tables(rrtm_text: str, rrtmg_text: str) -> dict:
    left = parse_rrtm_sw_v25_tables(rrtm_text)
    right = parse_rrtmg_sw_2007_tables(rrtmg_text)
    mismatches = []
    matched_values = 0
    for key in sorted(left):
        a, b = left[key], right[key]
        bad = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
        if bad:
            mismatches.append({"array": key, "indexes": bad})
        else:
            matched_values += len(a)
    return {
        "array_count": len(left),
        "matched_array_count": len(left) - len(mismatches),
        "value_count": sum(len(v) for v in left.values()),
        "matched_value_count": matched_values,
        "mismatches": mismatches,
        "continuity_qualified": not mismatches and len(left) == 56 and matched_values == 2576,
        "preaveraging_generator_recovered": False,
        "exact_historical_weighting_recovered": False,
        "original_aer_v25_tarball_hash_recovered": False,
    }
