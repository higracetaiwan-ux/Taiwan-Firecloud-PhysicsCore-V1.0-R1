"""Shared Taiwan dawn/dusk scenic-spot registry.

R5.7.41.3 centralizes the observation-location list used by PhysicsCore so
repeat CASE collection uses stable site identity rather than floating-point
coordinate matching.  The bundled registry is derived from the user's
Taiwan dawn/dusk photography master database V2.2.

This module is UI/metadata only.  Physics still consumes only latitude and
longitude; site metadata must never alter Formation, Viewing, Glow or COT.
"""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
from typing import Iterable

REGISTRY_VERSION = "TAIWAN_DAWN_DUSK_SCENIC_SPOTS_V2.2_187"
DEFAULT_SITE_ID = "TWS106"  # 台中市 高美濕地
REGISTRY_PATH = Path(__file__).resolve().parent / "data" / "scenic_spots_v2_2.json"
REGION_ORDER = ("北部", "中部", "南部", "花東", "離島")


def _region_for(county_area: str, name: str) -> str:
    text = f"{county_area} {name}"
    if any(token in text for token in ("澎湖", "金門", "馬祖", "連江", "綠島", "蘭嶼")):
        return "離島"
    if any(token in text for token in ("台東", "臺東", "花蓮")):
        return "花東"
    if any(token in text for token in ("嘉義", "台南", "臺南", "高雄", "屏東")):
        return "南部"
    if any(token in text for token in ("苗栗", "台中", "臺中", "彰化", "南投", "雲林")):
        return "中部"
    return "北部"


def _event_tokens(raw: str) -> tuple[str, ...]:
    text = str(raw or "")
    out: list[str] = []
    if "日出" in text or "晨昏" in text:
        out.append("sunrise")
    if "日落" in text or "晨昏" in text:
        out.append("sunset")
    return tuple(dict.fromkeys(out))


@lru_cache(maxsize=1)
def load_scenic_spots() -> tuple[dict, ...]:
    raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    spots: list[dict] = []
    for row in raw:
        number = int(row["編號"])
        name = str(row["景點／攝影機位"]).strip()
        county = str(row.get("縣市／地區", "")).strip()
        lat = float(row["緯度"])
        lon = float(row["經度"])
        site_id = f"TWS{number:03d}"
        spots.append({
            "site_id": site_id,
            "site_name": name,
            "site_region": _region_for(county, name),
            "site_county_area": county,
            "latitude": lat,
            "longitude": lon,
            "gps_status": str(row.get("GPS狀態", "")),
            "gps_type": str(row.get("GPS類型", "")),
            "event_suitability_raw": str(row.get("日出／日落", "")),
            "event_tokens": _event_tokens(str(row.get("日出／日落", ""))),
            "main_subject": str(row.get("主要題材", "")),
            "notes": str(row.get("備註", "")),
            "source": str(row.get("來源", "")),
            "registry_version": REGISTRY_VERSION,
        })
    return tuple(spots)


def scenic_spot_by_id(site_id: str | None) -> dict | None:
    wanted = str(site_id or "").strip().upper()
    return next((dict(s) for s in load_scenic_spots() if s["site_id"].upper() == wanted), None)


def match_scenic_spot(lat: float, lon: float, *, tolerance_deg: float = 1e-5) -> dict | None:
    lat = float(lat); lon = float(lon)
    best = None; best_d = None
    for spot in load_scenic_spots():
        d = abs(float(spot["latitude"]) - lat) + abs(float(spot["longitude"]) - lon)
        if best_d is None or d < best_d:
            best, best_d = spot, d
    if best is not None and best_d is not None and best_d <= float(tolerance_deg) * 2.0:
        return dict(best)
    return None


def scenic_regions() -> tuple[str, ...]:
    present = {s["site_region"] for s in load_scenic_spots()}
    return tuple(r for r in REGION_ORDER if r in present)


def filter_scenic_spots(*, region: str | None = None, event: str | None = None, compatible_only: bool = False) -> list[dict]:
    rows: Iterable[dict] = load_scenic_spots()
    if region and region != "全部":
        rows = [s for s in rows if s["site_region"] == region]
    if compatible_only and event in {"sunrise", "sunset"}:
        rows = [s for s in rows if event in s["event_tokens"]]
    return [dict(s) for s in rows]


def event_is_compatible(spot: dict | None, event: str) -> bool:
    if not spot:
        return True
    tokens = tuple(spot.get("event_tokens") or ())
    return not tokens or str(event) in tokens


def scenic_spot_label(spot: dict) -> str:
    suitability = str(spot.get("event_suitability_raw") or "未標記")
    county = str(spot.get("site_county_area") or spot.get("site_region") or "")
    return f"{county}｜{spot['site_name']}｜{suitability}"
