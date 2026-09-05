from pathlib import Path
import hashlib
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "hitran_runtime" / "firecloud_600_750nm_band_coefficients.csv"
MAN = ROOT / "hitran_runtime" / "firecloud_600_750nm_band_coefficients.manifest.json"

def test_packaged_lut_is_validated_432_row_six_band_runtime():
    df = pd.read_csv(CSV)
    manifest = json.loads(MAN.read_text(encoding="utf-8"))
    sha = hashlib.sha256(CSV.read_bytes()).hexdigest()
    assert len(df) == 432
    assert sorted(df["wavelength_nm"].astype(int).unique().tolist()) == [550, 575, 600, 650, 700, 750]
    assert sorted(df["gas"].unique().tolist()) == ["H2O", "O2", "O3"]
    assert sha == manifest["sha256"]
    assert manifest["rows"] == 432
    assert manifest["wavelengths_nm"] == [550, 575, 600, 650, 700, 750]
    counts = df.groupby(["gas", "wavelength_nm"]).size()
    assert (counts == 24).all()
    assert df["sigma_cm2_molecule"].notna().all()
