import hashlib
import json
from pathlib import Path

import pandas as pd

from firecloud.hitran_runtime import (
    EXPECTED_ROWS,
    MANIFEST_FILENAME,
    COEFFICIENT_FILENAME,
    install_runtime_lut,
    validate_runtime_lut_bytes,
)
from firecloud.hitran_readiness import inspect_hitran_coefficient_table, resolve_hitran_lut_path


def _valid_lut_bytes():
    rows=[]
    for gas in ("H2O","O3","O2"):
        for wl in (600,650,700,750):
            for t in (220,250,280,293):
                for p in (100,300,500,700,900,1000):
                    rows.append({
                        "wavelength_nm":wl,
                        "gas":gas,
                        "sigma_cm2_molecule":1e-25,
                        "temperature_k":t,
                        "pressure_hpa":p,
                        "spectroscopy_source":("SERDYUCHENKO_GORSHELEV_XSC_LINEAR_T" if gas=="O3" else "HITRAN_HAPI_VOIGT_LOCAL"),
                    })
    csv=pd.DataFrame(rows).to_csv(index=False).encode()
    manifest={"version":"V8.4.5","rows":len(rows),"sha256":hashlib.sha256(csv).hexdigest()}
    return csv, json.dumps(manifest).encode()


def test_strict_runtime_lut_requires_full_288_state_grid():
    csv, manifest=_valid_lut_bytes()
    audit=validate_runtime_lut_bytes(csv, manifest)
    assert audit["ok"] is True
    assert audit["rows"] == EXPECTED_ROWS == 288
    short=b"wavelength_nm,gas,sigma_cm2_molecule,temperature_k,pressure_hpa,spectroscopy_source\n600,H2O,1e-25,280,700,HITRAN\n"
    assert validate_runtime_lut_bytes(short)["ok"] is False


def test_install_runtime_lut_writes_only_derived_files(tmp_path):
    csv, manifest=_valid_lut_bytes()
    audit=install_runtime_lut(csv, manifest, tmp_path)
    assert audit["ok"] is True
    assert (tmp_path/COEFFICIENT_FILENAME).is_file()
    assert (tmp_path/MANIFEST_FILENAME).is_file()
    assert not list(tmp_path.glob("*.data"))
    assert not list(tmp_path.glob("*.header"))


def test_packaged_runtime_lut_is_resolved_without_hitran_db(tmp_path, monkeypatch):
    csv, manifest=_valid_lut_bytes()
    runtime=tmp_path/"runtime"; runtime.mkdir()
    audit=install_runtime_lut(csv, manifest, runtime)
    assert audit["ok"]
    monkeypatch.setenv("FIRECLOUD_HITRAN_LUT_PATH", str(runtime/COEFFICIENT_FILENAME))
    monkeypatch.delenv("FIRECLOUD_HITRAN_DB", raising=False)
    path, source=resolve_hitran_lut_path()
    assert path == runtime/COEFFICIENT_FILENAME
    assert source == "env:FIRECLOUD_HITRAN_LUT_PATH"
    s=inspect_hitran_coefficient_table()
    assert s["coefficient_table_complete"] is True
    assert s["coefficient_table_rows"] == 288
