from pathlib import Path
import hashlib
import json

import pandas as pd

import firecloud
from firecloud.ice_cloud_spectral_optics import (
    BUNDLED_CALIBRATED_LUT_PATH,
    ICE_OPTICS_WAVELENGTHS_NM,
    load_ice_optics_lut,
)


ROOT = Path(__file__).resolve().parents[1]
ICE_DATA = ROOT / "firecloud" / "data" / "ice_optics"


def test_release_version_and_bundled_portable_lut_is_explicitly_loadable():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.30.14"
    assert BUNDLED_CALIBRATED_LUT_PATH == ICE_DATA / "portable_ice_optics_lut_v1.csv"
    lut, status = load_ice_optics_lut(BUNDLED_CALIBRATED_LUT_PATH)
    assert status.loaded is True
    assert status.state == "ICE_OPTICS_LUT_READY"
    assert len(lut) == 30618
    assert set(lut["wavelength_nm"].round().astype(int)) == set(ICE_OPTICS_WAVELENGTHS_NM)
    groups = lut.groupby(["ice_habit", "surface_roughness", "maximum_dimension_um"], dropna=False).ngroups
    assert groups == 5103


def test_bundled_portable_lut_hash_matches_certified_portable_manifest():
    manifest = json.loads((ICE_DATA / "portable_manifest_v1_1.json").read_text(encoding="utf-8"))
    payload = (ICE_DATA / "portable_ice_optics_lut_v1.csv").read_bytes()
    got = hashlib.sha256(payload).hexdigest()
    assert got == manifest["files"]["ice_optics_lut_v1.csv"]["sha256"]
    assert manifest["primary_size_coordinate"] == "maximum_dimension_um"
    assert manifest["physics_promotion_allowed"] is False


def test_bundled_portable_release_artifact_matches_pinned_sha256():
    line = (ICE_DATA / "portable_package_v1_1.sha256").read_text(encoding="utf-8").strip()
    expected, filename = line.split(maxsplit=1)
    artifact = ROOT / "release_artifacts" / filename
    assert artifact.exists()
    assert hashlib.sha256(artifact.read_bytes()).hexdigest() == expected
    assert expected == "802d82b49cef4e20a4458bc50f063133a58b19fcfcb4e49941cc8ca16f7afd05"
