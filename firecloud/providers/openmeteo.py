from __future__ import annotations

from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import time
import requests
import pandas as pd


class OpenMeteoRateLimitError(requests.HTTPError):
    """Terminal HTTP 429 after bounded retries.

    The route fetcher catches this explicitly and opens a provider circuit for
    the remainder of the run so rate limiting cannot abort the full analysis.
    """


API_URL = "https://api.open-meteo.com/v1/forecast"

PRESSURE_LEVELS_HPA = (
    1000, 975, 950, 925, 900, 850, 800, 700, 600, 500,
    400, 300, 250, 200, 150, 100, 70, 50, 30,
)

SURFACE_HOURLY_VARS = [
    "cloud_cover_low", "cloud_cover_mid", "cloud_cover_high", "visibility",
    "precipitation", "surface_pressure", "relative_humidity_850hPa",
    "relative_humidity_700hPa", "relative_humidity_500hPa", "wind_speed_850hPa",
    "wind_direction_850hPa", "wind_speed_500hPa", "wind_direction_500hPa",
]

PRESSURE_PROFILE_VARS = []
for _p in PRESSURE_LEVELS_HPA:
    PRESSURE_PROFILE_VARS.extend([
        f"cloud_cover_{_p}hPa", f"temperature_{_p}hPa",
        f"relative_humidity_{_p}hPa", f"geopotential_height_{_p}hPa",
    ])
HOURLY_VARS = list(dict.fromkeys(SURFACE_HOURLY_VARS + PRESSURE_PROFILE_VARS))


def _chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i+n]


def _cache_dir() -> Path:
    raw = os.getenv("FIRECLOUD_OPENMETEO_CACHE_DIR", "").strip()
    if raw:
        return Path(raw).expanduser()
    # Persist across Streamlit reruns within the deployment checkout/runtime.
    return Path(__file__).resolve().parents[2] / ".cache" / "openmeteo_forecast"


def _cache_ttl_seconds() -> float:
    try:
        return max(0.0, float(os.getenv("FIRECLOUD_OPENMETEO_CACHE_TTL_SECONDS", "1800")))
    except Exception:
        return 1800.0


def _canonical_request_key(url: str, params: dict) -> str:
    payload = json.dumps({"url": url, "params": params}, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _load_cached_json(key: str):
    p = _cache_dir() / f"{key}.json"
    try:
        if not p.exists():
            return None
        ttl = _cache_ttl_seconds()
        if ttl > 0 and (time.time() - p.stat().st_mtime) > ttl:
            return None
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _save_cached_json(key: str, data) -> None:
    try:
        d = _cache_dir(); d.mkdir(parents=True, exist_ok=True)
        tmp = d / f".{key}.tmp"
        tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        tmp.replace(d / f"{key}.json")
    except Exception:
        pass


def _dedupe_query_points(points: list[dict]):
    """Collapse exact duplicate coordinates for provider I/O only.

    The observer at distance=0 exists once per direction offset and therefore used
    to be requested three times.  Keep every logical route point in the returned
    model frame, but query each exact coordinate only once and fan the response
    back out to all matching point_ids.
    """
    unique = []
    members = []
    by_key = {}
    for p in points:
        key = (round(float(p["lat"]), 8), round(float(p["lon"]), 8))
        idx = by_key.get(key)
        if idx is None:
            idx = len(unique); by_key[key] = idx
            unique.append(p); members.append([p])
        else:
            members[idx].append(p)
    return unique, members


def _backoff_cap_seconds() -> float:
    try:
        return max(2.0, float(os.getenv("FIRECLOUD_OPENMETEO_BACKOFF_CAP_SECONDS", "30")))
    except Exception:
        return 30.0


def _max_attempts() -> int:
    try:
        return max(1, min(6, int(os.getenv("FIRECLOUD_OPENMETEO_MAX_ATTEMPTS", "3"))))
    except Exception:
        return 3


def _sleep_with_optional_heartbeat(wait_s: float, status_callback=None, message: str = "") -> None:
    wait_s = max(0.0, float(wait_s))
    if status_callback is None:
        time.sleep(wait_s)
        return
    remaining = wait_s
    while remaining > 1e-9:
        try:
            status_callback(f"{message}；等待 {remaining:.0f}s")
        except Exception:
            pass
        step = min(5.0, remaining)
        time.sleep(step)
        remaining -= step


def _get_with_rate_limit_backoff(session: requests.Session, url: str, *, params: dict, timeout=(8, 30), max_attempts: int = 6, status_callback=None):
    last = None
    for attempt in range(1, max_attempts + 1):
        try:
            if status_callback is not None:
                status_callback(f"HTTP 請求 {attempt}/{max_attempts}")
            r = session.get(url, params=params, timeout=timeout)
        except requests.RequestException:
            raise
        last = r
        if r.status_code != 429:
            r.raise_for_status(); return r
        if attempt >= max_attempts:
            break
        retry_after = r.headers.get("Retry-After")
        try:
            wait_s = float(retry_after) if retry_after is not None else min(60.0, 4.0 * (2 ** (attempt - 1)))
        except (TypeError, ValueError):
            wait_s = min(60.0, 4.0 * (2 ** (attempt - 1)))
        wait_s = min(_backoff_cap_seconds(), max(2.0, wait_s))
        _sleep_with_optional_heartbeat(wait_s, status_callback, f"Open-Meteo HTTP 429，第 {attempt}/{max_attempts} 次")
    if last is not None:
        raise OpenMeteoRateLimitError(
            f"Open-Meteo HTTP 429 after {max_attempts} attempts",
            response=last,
        )
    raise requests.HTTPError("Open-Meteo request failed without a response")


def _placeholder_hourly_base(start: datetime, end: datetime, source: str, hourly_vars=None) -> pd.DataFrame:
    """Create an auditable Missing frame that preserves route/time geometry."""
    start_day = pd.Timestamp(start.date())
    end_exclusive = pd.Timestamp(end.date()) + pd.Timedelta(days=1)
    times = pd.date_range(start_day, end_exclusive, freq="h", inclusive="left")
    base = pd.DataFrame({"time": times})
    vars_used = list(HOURLY_VARS if hourly_vars is None else hourly_vars)
    for v in vars_used:
        base[v] = math.nan
    base["model_surface_elevation_m"] = math.nan
    base["vertical_profile_source"] = source
    return base


def _append_member_frames(frames: list, member_group: list[dict], base: pd.DataFrame) -> None:
    for p in member_group:
        df = base.copy()
        for k in ("point_id", "distance_km", "direction_offset_deg", "lat", "lon"):
            df[k] = p[k]
        frames.append(df)


def fetch_route_hourly(points: list[dict], start: datetime, end: datetime, timezone: str = "Asia/Taipei",
                       progress_callback=None, hourly_vars=None, batch_size: int | None = None,
                       request_profile: str = "FULL") -> pd.DataFrame:
    """Fetch route forecast with persistent cache and a 429 circuit breaker.

    V8.4.11.1 allows the caller to request only the lightweight operational
    surface fields.  The full pressure-level thermodynamic state is supplied by
    the already-downloaded native GFS GRIB whenever available.  Open-Meteo
    pressure levels are therefore a *deferred fallback*, not a mandatory first
    request.  Provider failure remains explicit Missing; it never becomes clear
    sky or a fabricated atmospheric profile.
    """
    vars_used = list(HOURLY_VARS if hourly_vars is None else hourly_vars)
    if batch_size is None:
        # Surface-only requests are much lighter than the historical 88-variable
        # pressure-profile request, so fewer HTTP calls are safer for the free API.
        batch_size = 30 if set(vars_used).issubset(set(SURFACE_HOURLY_VARS)) else 15
    batch_size=max(1,int(batch_size))
    frames = []
    audit = []
    session = requests.Session()
    unique_points, members = _dedupe_query_points(points)
    indexed = list(zip(unique_points, members))
    batches = list(_chunks(indexed, batch_size))
    rate_limit_circuit_open = False
    successful_unique_locations = 0
    missing_unique_locations = 0

    def _emit(batch_idx: int, message: str):
        if progress_callback is None:
            return
        try:
            progress_callback(batch_idx, len(batches), str(message))
        except Exception:
            pass

    for batch_idx, batch_pairs in enumerate(batches):
        batch = [x[0] for x in batch_pairs]
        batch_members = [x[1] for x in batch_pairs]
        params = {
            "latitude": ",".join(str(p["lat"]) for p in batch),
            "longitude": ",".join(str(p["lon"]) for p in batch),
            "hourly": ",".join(vars_used), "timezone": timezone,
            "start_date": start.date().isoformat(), "end_date": end.date().isoformat(),
        }
        key = _canonical_request_key(API_URL, params)
        data = _load_cached_json(key)
        cache_status = "HIT" if data is not None else "MISS"
        network_status = "CACHE_HIT" if data is not None else "PENDING"
        network_requested = False
        error_text = ""

        if data is None and rate_limit_circuit_open:
            network_status = "SKIPPED_RATE_LIMIT_CIRCUIT_OPEN"
            _emit(batch_idx, f"批次 {batch_idx+1}/{len(batches)}：429 circuit 已開啟，保留 Missing、不中止分析")
        elif data is None:
            network_requested = True
            _emit(batch_idx, f"批次 {batch_idx+1}/{len(batches)}：下載 {len(batch)} 個路徑點／{len(vars_used)} 欄位")
            try:
                # A 429 on the lightweight operational request is not worth
                # exponential retries inside the same analysis. Native GFS now
                # carries the pressure-profile physics, so fail fast to explicit
                # Missing and let a later resume/cache pass retry the surface data.
                attempts = 1 if str(request_profile).upper() == "SURFACE_ONLY" else _max_attempts()
                r = _get_with_rate_limit_backoff(
                    session, API_URL, params=params, timeout=(8, 30),
                    max_attempts=attempts,
                    status_callback=lambda msg, bi=batch_idx: _emit(bi, f"批次 {bi+1}/{len(batches)}：{msg}"),
                )
                data = r.json(); _save_cached_json(key, data)
                network_status = "OK"
            except OpenMeteoRateLimitError as exc:
                rate_limit_circuit_open = True
                network_status = "RATE_LIMIT_DEFERRED"
                error_text = f"{type(exc).__name__}: {exc}"
                _emit(batch_idx, f"批次 {batch_idx+1}/{len(batches)}：HTTP 429，停止本次後續 Open-Meteo 網路請求；缺失保持 Missing")
            except requests.RequestException as exc:
                network_status = "NETWORK_FAILED_MISSING"
                error_text = f"{type(exc).__name__}: {exc}"
                _emit(batch_idx, f"批次 {batch_idx+1}/{len(batches)}：網路失敗，該批次保持 Missing 並繼續")

        batch_missing = data is None
        if batch_missing:
            placeholder = _placeholder_hourly_base(start, end, "OPEN_METEO_PROVIDER_MISSING", vars_used)
            for member_group in batch_members:
                _append_member_frames(frames, member_group, placeholder)
            missing_unique_locations += len(batch)
        else:
            locations = data if isinstance(data, list) else [data]
            for loc_idx, member_group in enumerate(batch_members):
                loc = locations[loc_idx] if loc_idx < len(locations) else None
                if not isinstance(loc, dict) or not isinstance(loc.get("hourly"), dict):
                    placeholder = _placeholder_hourly_base(start, end, "OPEN_METEO_LOCATION_MISSING", vars_used)
                    _append_member_frames(frames, member_group, placeholder)
                    missing_unique_locations += 1
                    continue
                hourly = loc.get("hourly", {}); times = hourly.get("time", [])
                base = pd.DataFrame({"time": pd.to_datetime(times)})
                for v in vars_used:
                    values = hourly.get(v)
                    if values is None:
                        base[v] = math.nan
                    elif v.startswith("temperature_"):
                        base[v] = [float(x) + 273.15 if x is not None else math.nan for x in values]
                    else:
                        base[v] = values
                base["model_surface_elevation_m"] = loc.get("elevation", math.nan)
                base["vertical_profile_source"] = (
                    "OPEN_METEO_PRESSURE_LEVEL_FALLBACK" if any(v.startswith("temperature_") for v in vars_used)
                    else "OPEN_METEO_OPERATIONAL_SURFACE"
                )
                _append_member_frames(frames, member_group, base)
                successful_unique_locations += 1

        audit.append({
            "provider": "OPEN_METEO_FORECAST", "batch_index": batch_idx,
            "request_profile": str(request_profile),
            "cache_status": cache_status, "cache_key": key,
            "network_status": network_status, "network_requested": bool(network_requested),
            "rate_limit_circuit_open": bool(rate_limit_circuit_open),
            "error": error_text,
            "queried_unique_locations": len(batch),
            "logical_route_points": sum(len(m) for m in batch_members),
            "deduplicated_locations_saved": sum(len(m) for m in batch_members) - len(batch),
            "requested_variable_count": len(vars_used),
            "batch_size": int(batch_size),
            "start_date": params["start_date"], "end_date": params["end_date"],
        })
        if batch_idx < len(batches) - 1 and cache_status != "HIT" and data is not None:
            # Surface-only batches are already consolidated. Keep a small gap to
            # avoid burst traffic; pressure fallback remains more conservative.
            time.sleep(1.0 if set(vars_used).issubset(set(SURFACE_HOURLY_VARS)) else 2.5)

    out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    out.attrs["api_request_audit"] = audit
    out.attrs["request_profile"] = str(request_profile)
    out.attrs["requested_variables"] = vars_used
    out.attrs["logical_route_points"] = len(points)
    out.attrs["unique_query_locations"] = len(unique_points)
    out.attrs["successful_unique_locations"] = int(successful_unique_locations)
    out.attrs["missing_unique_locations"] = int(missing_unique_locations)
    out.attrs["rate_limit_deferred"] = bool(any(a.get("network_status") == "RATE_LIMIT_DEFERRED" for a in audit))
    out.attrs["openmeteo_status"] = (
        "PARTIAL_RATE_LIMIT" if out.attrs["rate_limit_deferred"] else
        ("PARTIAL_MISSING" if missing_unique_locations else "READY")
    )
    return out


def fetch_route_surface_hourly(points: list[dict], start: datetime, end: datetime, timezone: str = "Asia/Taipei", progress_callback=None) -> pd.DataFrame:
    """Lightweight operational Open-Meteo request used on the normal GFS-native path."""
    return fetch_route_hourly(points, start, end, timezone, progress_callback=progress_callback,
                              hourly_vars=SURFACE_HOURLY_VARS, batch_size=30, request_profile="SURFACE_ONLY")


def fetch_route_pressure_hourly(points: list[dict], start: datetime, end: datetime, timezone: str = "Asia/Taipei", progress_callback=None) -> pd.DataFrame:
    """Deferred heavy pressure-profile fallback used only when native GFS is unavailable."""
    return fetch_route_hourly(points, start, end, timezone, progress_callback=progress_callback,
                              hourly_vars=PRESSURE_PROFILE_VARS, batch_size=8, request_profile="PRESSURE_PROFILE_FALLBACK")


def interpolate_route_at_time(hourly_df: pd.DataFrame, when: datetime) -> pd.DataFrame:
    if hourly_df.empty:
        return hourly_df.copy()
    df = hourly_df; target = pd.Timestamp(when.replace(tzinfo=None))
    times = pd.DatetimeIndex(pd.to_datetime(df["time"], errors="coerce").dropna().unique()).sort_values()
    if len(times) == 0:
        return pd.DataFrame(columns=df.columns)
    if target <= times[0]:
        chosen = df[pd.to_datetime(df["time"]) == times[0]].copy(); chosen["time"] = target; return chosen.reset_index(drop=True)
    if target >= times[-1]:
        chosen = df[pd.to_datetime(df["time"]) == times[-1]].copy(); chosen["time"] = target; return chosen.reset_index(drop=True)
    pos = int(times.searchsorted(target, side="left")); t1 = times[pos]
    if t1 == target:
        chosen = df[pd.to_datetime(df["time"]) == t1].copy(); chosen["time"] = target; return chosen.reset_index(drop=True)
    t0 = times[pos - 1]
    a = df[pd.to_datetime(df["time"]) == t0].drop_duplicates("point_id", keep="last").set_index("point_id", drop=False)
    b = df[pd.to_datetime(df["time"]) == t1].drop_duplicates("point_id", keep="first").set_index("point_id", drop=False)
    ids = a.index.union(b.index, sort=False); a = a.reindex(ids); b = b.reindex(ids)
    total = (t1 - t0).total_seconds(); w = (target - t0).total_seconds() / total if total else 0.0
    out = a.copy(); cols = [c for c in HOURLY_VARS if c in a.columns and c in b.columns]
    if cols:
        av = a[cols].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
        bv = b[cols].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
        interp = av + float(w) * (bv - av)
        for j, col in enumerate(cols):
            out[col] = pd.Series(interp[:, j], index=out.index, dtype="float64")
    out["time"] = target
    return out.reset_index(drop=True)
