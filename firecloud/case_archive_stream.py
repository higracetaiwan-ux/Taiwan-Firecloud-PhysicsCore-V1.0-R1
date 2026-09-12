"""Bounded streaming helpers for CASE archive CSV members.

R5.7.41.3.4.6 moved the hot DataFrame→CSV→ZipExtFile path behind a bounded
UTF-8 coalescing writer. This module is engineering-only: it must preserve the
exact uncompressed CSV byte stream, SHA256, row count and Missing representation.
"""
from __future__ import annotations

import hashlib
from typing import Any

import pandas as pd

DEFAULT_BUFFER_BYTES = 4 * 1024 * 1024
DEFAULT_CHUNKSIZE = 8192


class BufferedHashingTextWriter:
    """TextIO-like adapter that hashes exact UTF-8 bytes and coalesces writes."""

    def __init__(self, raw: Any, *, buffer_bytes: int = DEFAULT_BUFFER_BYTES):
        self.raw = raw
        self.buffer_bytes = max(1, int(buffer_bytes))
        self.buffer = bytearray()
        self.digest = hashlib.sha256()
        self.byte_count = 0
        self.raw_write_count = 0
        self.max_buffer_observed = 0

    def _flush_buffer(self) -> None:
        if not self.buffer:
            return
        self.raw.write(self.buffer)
        self.raw_write_count += 1
        self.buffer.clear()

    def write(self, text: str) -> int:
        text = str(text)
        data = text.encode("utf-8")
        self.digest.update(data)
        self.byte_count += len(data)
        self.buffer.extend(data)
        self.max_buffer_observed = max(self.max_buffer_observed, len(self.buffer))
        if len(self.buffer) >= self.buffer_bytes:
            self._flush_buffer()
        return len(text)

    def flush(self) -> None:
        self._flush_buffer()

    def hexdigest(self) -> str:
        return self.digest.hexdigest()


def write_csv_member_stream(
    zf,
    arcname: str,
    df,
    *,
    chunksize: int = DEFAULT_CHUNKSIZE,
    buffer_bytes: int = DEFAULT_BUFFER_BYTES,
) -> dict:
    """Write one DataFrame as CSV into an open ZipFile without full CSV materialization."""
    frame = df if isinstance(df, pd.DataFrame) else pd.DataFrame()
    with zf.open(arcname, mode="w") as raw:
        writer = BufferedHashingTextWriter(raw, buffer_bytes=buffer_bytes)
        frame.to_csv(writer, index=False, chunksize=chunksize)
        writer.flush()
    return {
        "artifact": arcname,
        "status": "WRITTEN",
        "row_count": int(len(frame)),
        "byte_size": int(writer.byte_count),
        "sha256": writer.hexdigest(),
        "detail": "CSV uncompressed payload; bounded UTF-8 coalescing buffer",
        "stream_buffer_bytes": int(buffer_bytes),
        "stream_raw_write_count": int(writer.raw_write_count),
    }
