import hashlib
import io
import json
from pathlib import Path

import pandas as pd

from firecloud.gas_rt import active_gas_wavelengths
from firecloud.hitran_runtime import validate_runtime_lut_bytes
from firecloud.hitran_readiness import hitran_backend_status


def test_sparse_o2_band_coverage_rule_accepts_line_free_600nm_gap():
    boot = (Path(__file__).resolve().parents[1] / "bootstrap_hitran_local_db.py").read_text(encoding="utf-8")
    assert "MANUAL_PAR_TARGET_BAND_INSUFFICIENT" in boot
    assert "required_bands = DIAGNOSTIC_BANDS_NM if gas == \"H2O\" else (575.0, 650.0, 700.0, 750.0)" in boot


def _lut(wavelengths):
    rows = []
    for gas in ("H2O", "O3", "O2"):
        for wl in wavelengths:
            for t in (220, 250, 280, 293):
                for p in (100, 300, 500, 700, 900, 1000):
                    rows.append({
                        "wavelength_nm": wl,
                        "gas": gas,
                        "sigma_cm2_molecule": 1e-25,
                        "temperature_k": t,
                        "pressure_hpa": p,
                        "spectroscopy_source": (
                            "SERDYUCHENKO_GORSHELEV_XSC_LINEAR_T"
                            if gas == "O3" else "HITRAN_HAPI_VOIGT_LOCAL"
                        ),
                    })
    csv = pd.DataFrame(rows).to_csv(index=False).encode()
    manifest = {
        "version": "V8.4.16",
        "rows": len(rows),
        "sha256": hashlib.sha256(csv).hexdigest(),
        "wavelengths_nm": list(wavelengths),
    }
    return csv, json.dumps(manifest).encode()


def test_complete_extended_lut_validates_as_360_states():
    csv, manifest = _lut((575, 600, 650, 700, 750))
    audit = validate_runtime_lut_bytes(csv, manifest)
    assert audit["ok"] is True
    assert audit["expected_rows"] == audit["rows"] == 360
    assert audit["active_wavelengths_nm"] == [575.0, 600.0, 650.0, 700.0, 750.0]


def test_partial_575_lut_stays_on_base_runtime_grid():
    csv, _ = _lut((600, 650, 700, 750))
    base = pd.read_csv(io.BytesIO(csv))
    base = pd.concat([base, base.iloc[[0]].assign(wavelength_nm=575)], ignore_index=True)
    audit = validate_runtime_lut_bytes(base.to_csv(index=False).encode())
    assert audit["ok"] is False
    assert audit["expected_rows"] == 360


def test_runtime_wavelength_switch_requires_complete_575_tp_grid():
    csv, _ = _lut((600, 650, 700, 750))
    base = pd.read_csv(io.BytesIO(csv))
    assert active_gas_wavelengths(base) == (600, 650, 700, 750)
    partial = pd.concat([base, base.iloc[[0]].assign(wavelength_nm=575)], ignore_index=True)
    assert active_gas_wavelengths(partial) == (600, 650, 700, 750)


def test_explicit_build_audit_does_not_fall_back_to_packaged_lut(tmp_path):
    csv, manifest = _lut((575, 600, 650, 700, 750))
    db = Path(tmp_path)
    (db / "firecloud_600_750nm_band_coefficients.csv").write_bytes(csv)
    (db / "firecloud_600_750nm_band_coefficients.manifest.json").write_bytes(manifest)
    status = hitran_backend_status(db_path=db)
    assert status["coefficient_table_source"] == "explicit"
    assert status["coefficient_table_rows"] == 360
    assert status["extended_runtime_spectroscopy_ready"] is True
