from pathlib import Path


def test_manual_par_import_uses_defined_numax_name():
    text = (Path(__file__).resolve().parents[1] / "bootstrap_hitran_local_db.py").read_text(encoding="utf-8")
    assert "NUMMAX" not in text
    assert "NUMAX = 1e7 / 560.0" in text
    assert "range=[{NUMIN:.2f},{NUMAX:.2f}]cm^-1" in text
