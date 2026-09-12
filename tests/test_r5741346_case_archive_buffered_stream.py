import hashlib
import io
import zipfile

import pandas as pd

from firecloud.case_archive_stream import (
    DEFAULT_TEXT_BUFFER_BYTES,
    _BufferedHashingTextWriter,
    write_dataframe_csv_member,
)


def test_buffered_case_csv_member_preserves_exact_utf8_payload_hash_and_size():
    frame = pd.DataFrame([
        {"name": "三仙台", "value": 1.25, "state": "DIRECT_EVIDENCE_CONFLICT"},
        {"name": "永鎮海濱", "value": None, "state": "MISSING"},
    ])
    expected = frame.to_csv(index=False).encode("utf-8")
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as zf:
        meta = write_dataframe_csv_member(zf, "x.csv", frame, buffer_bytes=32)
    mem.seek(0)
    with zipfile.ZipFile(mem) as zf:
        actual = zf.read("x.csv")
    assert actual == expected
    assert meta["byte_size"] == len(expected)
    assert meta["sha256"] == hashlib.sha256(expected).hexdigest()
    assert meta["row_count"] == 2


def test_buffered_writer_coalesces_many_small_text_writes_without_payload_change():
    class Raw:
        def __init__(self):
            self.parts = []
        def write(self, data):
            self.parts.append(bytes(data))
            return len(data)

    raw = Raw()
    digest = hashlib.sha256()
    writer = _BufferedHashingTextWriter(raw, digest=digest, buffer_bytes=64)
    pieces = [f"row-{i:03d},資料\n" for i in range(100)]
    for piece in pieces:
        assert writer.write(piece) == len(piece)
    writer.flush()
    expected = "".join(pieces).encode("utf-8")
    assert b"".join(raw.parts) == expected
    assert digest.hexdigest() == hashlib.sha256(expected).hexdigest()
    assert writer.byte_count == len(expected)
    assert writer.raw_write_count < len(pieces)


def test_default_case_stream_buffer_is_bounded_four_mib_and_empty_frame_is_valid():
    assert DEFAULT_TEXT_BUFFER_BYTES == 4 * 1024 * 1024
    frame = pd.DataFrame()
    expected = frame.to_csv(index=False).encode("utf-8")
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as zf:
        meta = write_dataframe_csv_member(zf, "empty.csv", frame)
    mem.seek(0)
    with zipfile.ZipFile(mem) as zf:
        assert zf.read("empty.csv") == expected
    assert meta["byte_size"] == len(expected)
    assert meta["sha256"] == hashlib.sha256(expected).hexdigest()
