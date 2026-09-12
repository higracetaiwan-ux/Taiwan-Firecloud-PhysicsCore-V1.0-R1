"""Historical NOAA GFS 0.25° GRIB2 retrieval via public object storage.

R5.7.41.3.4 adds a transport fallback for runs that have aged out of the
NOMADS GRIB filter window while preserving the exact frozen GFS cycle/lead and
native-field semantics.  The provider reads the public ``.idx`` sidecar, selects
only requested GRIB messages, and downloads those byte ranges from NOAA's AWS
Open Data object instead of downloading the full global GRIB2 file.

Scientific contract
-------------------
* transport-only fallback; cycle/lead are never re-resolved here;
* no RH/cloud-fraction -> condensate inference;
* no spatial or vertical interpolation of native condensate;
* Missing remains Missing if the archive/object/index/required messages are
  unavailable;
* range responses must be HTTP 206; a server that ignores Range is rejected so
  a full 200--500 MB global file cannot be downloaded accidentally.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import os
import re
import tempfile
from typing import Iterable

import requests

from ..runtime_hardening import stamp_cache_artifact, cache_provenance

AWS_GFS_BASE_URL = "https://noaa-gfs-bdp-pds.s3.amazonaws.com"
TRANSPORT_NAME = "NOAA_GFS_AWS_IDX_HTTP_RANGE"
SCHEMA_VERSION = "R5.7.41.3.4_GFS_AWS_IDX_RANGE_V1"

_MB_LEVEL_RE = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)\s*mb\b", re.IGNORECASE)


@dataclass(frozen=True)
class GribIndexRecord:
    message_number: int
    start_byte: int
    variable: str
    level_text: str
    raw_line: str
    end_byte: int | None = None

    @property
    def byte_count(self) -> int | None:
        if self.end_byte is None:
            return None
        return int(self.end_byte - self.start_byte + 1)


@dataclass(frozen=True)
class ByteSpan:
    start_byte: int
    end_byte: int | None
    selected_message_count: int
    selected_payload_bytes: int | None

    @property
    def byte_count(self) -> int | None:
        if self.end_byte is None:
            return None
        return int(self.end_byte - self.start_byte + 1)


def build_object_urls(run: datetime, lead_hour: int, product: str = "pgrb2.0p25",
                      base_url: str | None = None) -> tuple[str, str]:
    base = str(base_url or os.getenv("FIRECLOUD_GFS_AWS_BASE_URL", "") or AWS_GFS_BASE_URL).rstrip("/")
    root = f"gfs.{run:%Y%m%d}/{run:%H}/atmos/gfs.t{run:%H}z.{product}.f{int(lead_hour):03d}"
    data_url = f"{base}/{root}"
    return data_url, data_url + ".idx"


def parse_grib_index(text: str) -> list[GribIndexRecord]:
    """Parse the NCEP/NOAA colon-delimited GRIB2 ``.idx`` format.

    Typical line::
      120:12345678:d=2026091200:CLWMR:500 mb:12 hour fcst:

    Only fields needed for byte routing are interpreted. Unknown/short lines are
    ignored rather than guessed.
    """
    prelim: list[GribIndexRecord] = []
    for raw in str(text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split(":")
        if len(parts) < 5:
            continue
        try:
            msg = int(parts[0])
            start = int(parts[1])
        except Exception:
            continue
        variable = str(parts[3]).strip().upper()
        level_text = str(parts[4]).strip()
        if not variable:
            continue
        prelim.append(GribIndexRecord(msg, start, variable, level_text, line, None))
    prelim.sort(key=lambda r: r.start_byte)
    out: list[GribIndexRecord] = []
    for i, rec in enumerate(prelim):
        end = prelim[i + 1].start_byte - 1 if i + 1 < len(prelim) else None
        out.append(GribIndexRecord(rec.message_number, rec.start_byte, rec.variable, rec.level_text, rec.raw_line, end))
    return out


def _level_hpa(level_text: str) -> float | None:
    m = _MB_LEVEL_RE.match(str(level_text or ""))
    if not m:
        return None
    try:
        return float(m.group(1))
    except Exception:
        return None


def select_pressure_messages(records: Iterable[GribIndexRecord], variables: Iterable[str],
                             pressure_levels_hpa: Iterable[float]) -> list[GribIndexRecord]:
    vars_wanted = {str(v).upper() for v in variables}
    levels = {round(float(x), 6) for x in pressure_levels_hpa}
    out = []
    for rec in records:
        if rec.variable.upper() not in vars_wanted:
            continue
        level = _level_hpa(rec.level_text)
        if level is None or round(level, 6) not in levels:
            continue
        out.append(rec)
    return out


def _resolve_last_end(records: list[GribIndexRecord], total_size: int | None) -> list[GribIndexRecord]:
    if not records:
        return []
    if records[-1].end_byte is not None or total_size is None:
        return records
    if int(total_size) <= records[-1].start_byte:
        return records
    out = list(records)
    r = out[-1]
    out[-1] = GribIndexRecord(r.message_number, r.start_byte, r.variable, r.level_text, r.raw_line, int(total_size) - 1)
    return out


def _merge_selected_spans(selected: list[GribIndexRecord], *, max_gap_bytes: int = 1_000_000,
                          max_span_bytes: int = 16_000_000) -> list[ByteSpan]:
    """Merge nearby selected messages while keeping bounded extra download bytes.

    The gap may include unselected complete GRIB messages. That is safe because
    ecCodes later ignores fields outside the requested contract.  The bounds are
    purely an HTTP-efficiency optimization and do not alter scientific evidence.
    """
    if not selected:
        return []
    selected = sorted(selected, key=lambda r: r.start_byte)
    spans: list[ByteSpan] = []
    cur_start = selected[0].start_byte
    cur_end = selected[0].end_byte
    cur_count = 1
    cur_payload = selected[0].byte_count
    for rec in selected[1:]:
        if cur_end is None:
            spans.append(ByteSpan(cur_start, cur_end, cur_count, cur_payload))
            cur_start, cur_end, cur_count, cur_payload = rec.start_byte, rec.end_byte, 1, rec.byte_count
            continue
        gap = rec.start_byte - cur_end - 1
        proposed_end = rec.end_byte
        proposed_span_bytes = None if proposed_end is None else proposed_end - cur_start + 1
        can_merge = gap >= 0 and gap <= max(0, int(max_gap_bytes))
        if proposed_span_bytes is not None and proposed_span_bytes > max(1, int(max_span_bytes)):
            can_merge = False
        if can_merge:
            cur_end = proposed_end
            cur_count += 1
            if cur_payload is None or rec.byte_count is None:
                cur_payload = None
            else:
                cur_payload += rec.byte_count
        else:
            spans.append(ByteSpan(cur_start, cur_end, cur_count, cur_payload))
            cur_start, cur_end, cur_count, cur_payload = rec.start_byte, rec.end_byte, 1, rec.byte_count
    spans.append(ByteSpan(cur_start, cur_end, cur_count, cur_payload))
    return spans


def _content_length_from_head(session, data_url: str) -> int | None:
    try:
        r = session.head(data_url, timeout=(8, 20), allow_redirects=True)
        if int(getattr(r, "status_code", 0) or 0) >= 400:
            return None
        raw = (getattr(r, "headers", {}) or {}).get("Content-Length")
        return int(raw) if raw is not None else None
    except Exception:
        return None


def _response_bytes(response) -> bytes:
    status = int(getattr(response, "status_code", 0) or 0)
    if status != 206:
        # Never consume a HTTP-200 body here: that could be the complete global
        # GFS file if an intermediary ignored the Range header.
        try:
            response.close()
        except Exception:
            pass
        raise RuntimeError(f"GFS AWS archive ignored/failed byte Range request (HTTP {status}; expected 206)")
    data = bytes(getattr(response, "content", b"") or b"")
    if len(data) < 8 or not data.startswith(b"GRIB"):
        raise RuntimeError(f"GFS AWS byte range is not a GRIB message span ({len(data)} bytes)")
    if not data.endswith(b"7777"):
        raise RuntimeError("GFS AWS byte range ended outside a complete GRIB2 message")
    return data


def download_message_subset(*, run: datetime, lead_hour: int, product: str,
                            variables: Iterable[str], pressure_levels_hpa: Iterable[float],
                            output_path: str | Path, session=None,
                            base_url: str | None = None) -> dict:
    """Download selected pressure-level messages from a public NOAA GFS object.

    Returns transport metadata/audit. Raises when the archive object/index is
    absent or when no requested messages exist; callers retain normal Missing
    semantics and may expose the failure in CASE audits.
    """
    s = session or requests.Session()
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    data_url, idx_url = build_object_urls(run, lead_hour, product, base_url=base_url)

    idx_resp = s.get(idx_url, timeout=(8, 25))
    idx_resp.raise_for_status()
    idx_text = getattr(idx_resp, "text", None)
    if idx_text is None:
        idx_text = bytes(getattr(idx_resp, "content", b"") or b"").decode("utf-8", errors="replace")
    records = parse_grib_index(idx_text)
    if not records:
        raise RuntimeError("GFS AWS .idx contained no parseable GRIB records")

    total_size = _content_length_from_head(s, data_url)
    records = _resolve_last_end(records, total_size)
    selected = select_pressure_messages(records, variables, pressure_levels_hpa)
    if not selected:
        raise RuntimeError("GFS AWS .idx contained no requested pressure-level messages")

    try:
        max_gap = int(os.getenv("FIRECLOUD_GFS_AWS_RANGE_MAX_GAP_BYTES", "1000000"))
    except Exception:
        max_gap = 1_000_000
    try:
        max_span = int(os.getenv("FIRECLOUD_GFS_AWS_RANGE_MAX_SPAN_BYTES", "16000000"))
    except Exception:
        max_span = 16_000_000
    spans = _merge_selected_spans(selected, max_gap_bytes=max_gap, max_span_bytes=max_span)

    known_download_bytes = sum(int(x.byte_count or 0) for x in spans if x.byte_count is not None)
    try:
        max_total = int(os.getenv("FIRECLOUD_GFS_AWS_MAX_DOWNLOAD_BYTES", str(512 * 1024 * 1024)))
    except Exception:
        max_total = 512 * 1024 * 1024
    if spans and all(x.byte_count is not None for x in spans) and known_download_bytes > max_total:
        raise RuntimeError(
            f"GFS AWS selected byte ranges exceed safety limit: {known_download_bytes} > {max_total}"
        )

    fd, tmp_name = tempfile.mkstemp(prefix=f".{out.name}.", suffix=".tmp", dir=str(out.parent))
    os.close(fd)
    tmp = Path(tmp_name)
    actual_bytes = 0
    range_audit: list[dict] = []
    try:
        with tmp.open("wb") as fh:
            for i, span in enumerate(spans, start=1):
                end_part = "" if span.end_byte is None else str(int(span.end_byte))
                range_header = f"bytes={int(span.start_byte)}-{end_part}"
                r = s.get(data_url, headers={"Range": range_header}, timeout=(8, 60), stream=True)
                data = _response_bytes(r)
                fh.write(data)
                actual_bytes += len(data)
                range_audit.append({
                    "range_index": i,
                    "range_header": range_header,
                    "http_status": int(getattr(r, "status_code", 0) or 0),
                    "bytes": len(data),
                    "selected_message_count": int(span.selected_message_count),
                })
                if actual_bytes > max_total:
                    raise RuntimeError(f"GFS AWS range download exceeded safety limit: {actual_bytes} > {max_total}")
            fh.flush()
            try:
                os.fsync(fh.fileno())
            except Exception:
                pass
        if actual_bytes < 1000:
            raise RuntimeError(f"GFS AWS selected GRIB payload unexpectedly small ({actual_bytes} bytes)")
        os.replace(tmp, out)
    except Exception:
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass
        raise

    stamp_cache_artifact(out, provider=TRANSPORT_NAME, role="RAW_GRIB_RANGE_SUBSET", schema=SCHEMA_VERSION, qc_state="CACHE_READY")
    prov = cache_provenance(out, provider=TRANSPORT_NAME, role="RAW_GRIB_RANGE_SUBSET", cache_status="DOWNLOAD")
    selected_payload = sum(int(x.byte_count or 0) for x in selected if x.byte_count is not None)
    return {
        "transport": TRANSPORT_NAME,
        "transport_schema_version": SCHEMA_VERSION,
        "source_base_url": str(base_url or os.getenv("FIRECLOUD_GFS_AWS_BASE_URL", "") or AWS_GFS_BASE_URL),
        "data_url": data_url,
        "idx_url": idx_url,
        "product": product,
        "idx_record_count": len(records),
        "selected_message_count": len(selected),
        "range_request_count": len(spans),
        "selected_payload_bytes": selected_payload,
        "downloaded_bytes": actual_bytes,
        "full_object_size_bytes": total_size,
        "range_audit": range_audit,
        **{k: v for k, v in prov.items() if str(k).startswith("cache_") or k in {"current_job_id", "current_run_mode"}},
    }
