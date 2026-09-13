from __future__ import annotations

import ast
import hashlib
import io
import zipfile
from pathlib import Path

import pandas as pd

import firecloud
from firecloud.case_archive_stream import write_csv_member_stream


ROOT = Path(__file__).resolve().parents[1]


def test_version_bumped_for_deployment_import_hotfix():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.9.2"


def test_app_guards_case_archive_stream_import_with_local_fallback():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    guarded = False
    fallback_def = False
    for node in tree.body:
        if isinstance(node, ast.Try):
            imported = any(
                isinstance(stmt, ast.ImportFrom)
                and stmt.module == "firecloud.case_archive_stream"
                and any(alias.name == "write_csv_member_stream" for alias in stmt.names)
                for stmt in node.body
            )
            catches_import = any(
                isinstance(handler.type, ast.Tuple)
                and {elt.id for elt in handler.type.elts if isinstance(elt, ast.Name)}
                >= {"ImportError", "ModuleNotFoundError"}
                for handler in node.handlers
            )
            local_defs = [
                stmt for handler in node.handlers for stmt in handler.body
                if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef))
                and stmt.name == "write_csv_member_stream"
            ]
            if imported and catches_import and local_defs:
                guarded = True
                fallback_def = True
                break
    assert guarded and fallback_def



def test_local_fallback_executes_and_preserves_exact_csv_when_helper_import_fails(monkeypatch):
    import builtins

    source = (ROOT / "app.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    target_try = None
    for node in tree.body:
        if isinstance(node, ast.Try) and any(
            isinstance(stmt, ast.ImportFrom)
            and stmt.module == "firecloud.case_archive_stream"
            for stmt in node.body
        ):
            target_try = node
            break
    assert target_try is not None

    real_import = builtins.__import__

    def blocked_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "firecloud.case_archive_stream":
            raise ImportError("simulated mixed-deploy helper mismatch")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", blocked_import)
    ns = {"hashlib": hashlib, "pd": pd}
    exec(compile(ast.Module(body=[target_try], type_ignores=[]), str(ROOT / "app.py"), "exec"), ns)
    fallback = ns["write_csv_member_stream"]

    frame = pd.DataFrame({"a": [1, 2], "b": ["測試", None]})
    expected = frame.to_csv(index=False).encode("utf-8")
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        meta = fallback(zf, "x.csv", frame, chunksize=1, buffer_bytes=7)
    with zipfile.ZipFile(io.BytesIO(mem.getvalue()), "r") as zf:
        actual = zf.read("x.csv")
    assert actual == expected
    assert meta["sha256"] == hashlib.sha256(expected).hexdigest()
    assert meta["byte_size"] == len(expected)

def test_canonical_stream_writer_preserves_exact_dataframe_csv_payload():
    frame = pd.DataFrame({"a": [1, 2], "b": ["測試", None]})
    expected = frame.to_csv(index=False).encode("utf-8")
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        meta = write_csv_member_stream(zf, "x.csv", frame, chunksize=1, buffer_bytes=7)
    with zipfile.ZipFile(io.BytesIO(mem.getvalue()), "r") as zf:
        actual = zf.read("x.csv")
    assert actual == expected
    assert meta["byte_size"] == len(expected)
    assert meta["sha256"] == hashlib.sha256(expected).hexdigest()
    assert meta["row_count"] == len(frame)
