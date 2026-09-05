from pathlib import Path
import importlib.util
import json
import hashlib
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("builder_r481", ROOT / "build_hitran_band_coefficients.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

TEMPS=[220.0,250.0,280.0,293.0]
PRESS=[100.0,300.0,500.0,700.0,900.0,1000.0]
BANDS=[575.0,600.0,650.0,700.0,750.0]

def _base(tmp_path):
    rows=[]
    for gas in ["H2O","O2","O3"]:
        for wl in BANDS:
            for t in TEMPS:
                for p in PRESS:
                    rows.append({
                        "wavelength_nm":wl,"gas":gas,"sigma_cm2_molecule":1e-25,
                        "temperature_k":t,"pressure_hpa":p,"band_half_width_nm":12.5,
                        "spectroscopy_source":"TEST","source_table":"TEST"
                    })
    csv=tmp_path/"base.csv"
    pd.DataFrame(rows).to_csv(csv,index=False)
    sha=hashlib.sha256(csv.read_bytes()).hexdigest()
    man=tmp_path/"base.manifest.json"
    man.write_text(json.dumps({"sha256":sha,"rows":360,"wavelengths_nm":[575,600,650,700,750]}))
    return csv,man

def test_incremental_base_validation_accepts_exact_360_row_contract(tmp_path):
    csv,man=_base(tmp_path)
    df=mod._validate_incremental_base_lut(csv,man,temperatures=TEMPS,pressures=PRESS)
    assert len(df)==360
    assert set(df.wavelength_nm)==set(BANDS)

def test_incremental_base_manifest_sha_is_enforced(tmp_path):
    csv,man=_base(tmp_path)
    man.write_text(json.dumps({"sha256":"0"*64}))
    with pytest.raises(SystemExit):
        mod._validate_incremental_base_lut(csv,man,temperatures=TEMPS,pressures=PRESS)

def test_r481_builder_computes_only_550_in_incremental_mode():
    text=(ROOT/"build_hitran_band_coefficients.py").read_text(encoding="utf-8")
    assert "build_wavelengths = [550.0]" in text
    assert "INCREMENTAL_BASE_VALIDATED" in text
    assert "never interpolate 550 nm" in text

def test_app_wires_packaged_validated_runtime_as_incremental_base():
    text=(ROOT/"app.py").read_text(encoding="utf-8")
    assert '"--incremental-base-lut"' in text
    assert '"--incremental-base-manifest"' in text
    assert "只計算 550 nm（72 rows）" in text
