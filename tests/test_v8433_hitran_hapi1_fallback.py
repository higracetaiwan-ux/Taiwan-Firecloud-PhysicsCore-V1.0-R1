from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]


def test_version_and_primary_hapi1_contract():
    init = (ROOT / "firecloud" / "__init__.py").read_text()
    assert 'PROGRAM_NAME = "Taiwan Firecloud PhysicsCore V1.0"' in init
    assert '__version__ = "1.0.0-R5.' in init
    text = (ROOT / "bootstrap_hitran_local_db.py").read_text()
    assert "def _download_with_hapi1" in text
    assert "hapi.fetch_by_ids(table, ids, NUMIN, NUMAX)" in text
    assert 'FIRECLOUD_HITRAN_ALLOW_HAPI2_FALLBACK' in text


def test_official_isotopologue_ids_are_pinned():
    tree = ast.parse((ROOT / "bootstrap_hitran_local_db.py").read_text())
    ns = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "HAPI1_ISO_IDS":
                    ns[target.id] = ast.literal_eval(node.value)
    assert ns["HAPI1_ISO_IDS"] == {
        "H2O": [1, 2, 3, 4, 5, 6, 129],
        "O3": [16, 17, 18, 19, 20],
        "O2": [36, 37, 38],
    }


def test_lut_manifest_version_updated():
    text = (ROOT / "build_hitran_band_coefficients.py").read_text()
    assert '"version":"PhysicsCore-V1.0-R4.8.2"' in text
