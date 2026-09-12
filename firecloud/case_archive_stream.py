"""Memory-bounded CASE CSV ZIP streaming helpers.

R5.7.41.3.4.6 keeps the CSV payload and manifest hash semantics identical to
legacy direct ZipExtFile streaming while coalescing many tiny UTF-8 writes into
bounded binary chunks before they enter zlib.
"""
from __future__ import annotations

import hashlib
from typing import Any

import pandas as pd

DEFAULT_TEXT_BUFFER_BYTES = 4 * 1024 * 1024
DEFAULT_CSV_CHUNKSIZE = 8192


class _BufferedHashingTextWriter:
    """Text writer that hashes exact UTF-8 payload bytes and coalesces writes.

    pandas ``to_csv`` may issue many small ``write(str)`` calls.  Writing each
    call directly to ``ZipExtFile`` creates avoidable Python/zlib overhead.  The
    buffer is bounded and does not materialize the complete CSV payload.
    """

    def __init__(self, raw: Any, *, digest: Any, buffer_bytes: int = DEFAULT_TEXT_BUFFER_BYTES):
        self.raw = raw
        self.digest = digest
        self.buffer_bytes = max(1, int(buffer_bytes))
        self.byte_count = 0
        self.raw_write_count = 0
        self._buffer = bytearray()

    def _flush_buffer(self) -> None:
        if not self._buffer:
            return
        self.raw.write(self._buffer)
        self.raw_write_count += 1
        self._buffer.clear()

    def write(self, text: Any) -> int:
        text = str(text)
        data = text.encode("utf-8")
        self.digest.update(data)
        self.byte_count += len(data)

        if len(data) >= self.buffer_bytes:
            self._flush_buffer()
            self.raw.write(data)
            self.raw_write_count += 1
        else:
            self._buffer.extend(data)
            if len(self._buffer) >= self.buffer_bytes:
                self._flush_buffer()
        return len(text)

    def flush(self) -> None:
        self._flush_buffer()


def write_dataframe_csv_member(
    zf: Any,
    arcname: str,
    df: Any,
    *,
    chunksize: int = DEFAULT_CSV_CHUNKSIZE,
    buffer_bytes: int = DEFAULT_TEXT_BUFFER_BYTES,
) -> dict[str, Any]:
    """Stream one DataFrame as UTF-8 CSV into an open ZipFile member.

    Returns integrity metadata for the **uncompressed CSV payload**.  No full
    CSV string/bytes object is constructed in memory.
    """
    frame = df if isinstance(df, pd.DataFrame) else pd.DataFrame()
    digest = hashlib.sha256()

    with zf.open(arcname, mode="w") as raw:
        writer = _BufferedHashingTextWriter(raw, digest=digest, buffer_bytes=buffer_bytes)
        frame.to_csv(writer, index=False, chunksize=chunksize)
        writer.flush()
        byte_count = int(writer.byte_count)
        raw_write_count = int(writer.raw_write_count)

    return {
        "artifact": arcname,
        "status": "WRITTEN",
        "row_count": int(len(frame)),
        "byte_size": byte_count,
        "sha256": digest.hexdigest(),
        "detail": "CSV uncompressed payload",
    }
