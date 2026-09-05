import os
from pathlib import Path

import pandas as pd

from firecloud.hitran_readiness import inspect_hitran_coefficient_table, hitran_backend_status


def _write_complete_lut(db: Path):
    rows=[]
    for gas in ("H2O","O3","O2"):
        for wl in (600,650,700,750):
            for t in (220,250,280,293):
                for p in (100,300,500,700,900,1000):
                    rows.append({
                        "wavelength_nm": wl,
                        "gas": gas,
                        "sigma_cm2_molecule": 1e-25,
                        "temperature_k": t,
                        "pressure_hpa": p,
                        "spectroscopy_source": ("SERDYUCHENKO_GORSHELEV_XSC_LINEAR_T" if gas=="O3" else "HITRAN_HAPI_VOIGT_LOCAL"),
                    })
    pd.DataFrame(rows).to_csv(db / "firecloud_600_750nm_band_coefficients.csv", index=False)


def test_empty_explicit_lut_is_not_spectroscopy_ready(tmp_path, monkeypatch):
    monkeypatch.setenv("FIRECLOUD_HITRAN_LUT_PATH", str(tmp_path / "missing.csv"))
    s=hitran_backend_status()
    assert s["coefficient_table_exists"] is False
    assert s["runtime_spectroscopy_ready"] is False
    assert s["runtime_spectroscopy_ready"] is False
    assert s["gas_rt_status"] == "HITRAN_COEFFICIENT_LUT_REQUIRED"


def test_complete_lut_is_runtime_ready_even_without_builder_state(tmp_path, monkeypatch):
    _write_complete_lut(tmp_path)
    monkeypatch.setenv("FIRECLOUD_HITRAN_DB", str(tmp_path))
    s=inspect_hitran_coefficient_table()
    assert s["coefficient_table_complete"] is True
    assert all(s["required_pair_status"].values())


def test_incomplete_lut_fails_closed(tmp_path, monkeypatch):
    pd.DataFrame([{
        "wavelength_nm":600,
        "gas":"H2O",
        "sigma_cm2_molecule":1e-25,
        "spectroscopy_source":"HITRAN_HAPI_VOIGT_LOCAL",
    }]).to_csv(tmp_path / "firecloud_600_750nm_band_coefficients.csv", index=False)
    monkeypatch.setenv("FIRECLOUD_HITRAN_LUT_PATH", str(tmp_path / "firecloud_600_750nm_band_coefficients.csv"))
    s=hitran_backend_status()
    assert s["runtime_spectroscopy_ready"] is False
    assert s["gas_rt_status"] == "HITRAN_COEFFICIENT_LUT_INCOMPLETE"
