import io
import tarfile
from pathlib import Path

from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import (
    build_fu96_rrtmg_band_weighting_provenance_evidence,
    build_fu96_rrtmg_band_weighting_provenance_gate,
    fu96_rrtmg_band_weighting_provenance_contract_payload,
)
from tools.verify_aer_rrtm_sw_v25_archive import inspect_archive, OFFICIAL_URL

EXPECTED_STATE = "PASS_FAIL_CLOSED_FU96_LINEAGE_BROADBAND_WEIGHTING_EQUATION_TRANSCRIPTION_CORRECTED_EXACT_RRTM_BAND24_25_REALIZATION_UNRECOVERED"


def test_step3q12_official_endpoint_historical_ftp_and_secondary_footprint_are_pinned():
    e = build_fu96_rrtmg_band_weighting_provenance_evidence().set_index("check_id")
    assert e.loc["AER_OFFICIAL_RRTM_SW_V25_BINARY_DOWNLOAD_ENDPOINT_PINNED", "status"] == "PASS_PINNED"
    assert "files.aer.com/rtweb/aer_rrtm_sw/aer_rrtm_sw_v2.5.tar.gz" in e.loc["AER_OFFICIAL_RRTM_SW_V25_BINARY_DOWNLOAD_ENDPOINT_PINNED", "observed"]
    assert e.loc["AER_RRTM_SW_V25_HISTORICAL_FTP_DISTRIBUTION_PATH_PINNED", "status"] == "PASS_PINNED"
    assert e.loc["RRTM_SW_V25_INDEPENDENT_EXTRACTED_DISTRIBUTION_FOOTPRINT", "status"] == "PASS_SECONDARY_QUALIFIED"
    assert "VERSION = v2.5" in e.loc["RRTM_SW_V25_INDEPENDENT_EXTRACTED_DISTRIBUTION_FOOTPRINT", "observed"]


def test_step3q12_lineage_gain_keeps_original_archive_and_physics_fail_closed():
    g = build_fu96_rrtmg_band_weighting_provenance_gate().iloc[0]
    assert bool(g["AER_OFFICIAL_RRTM_SW_V25_BINARY_DOWNLOAD_ENDPOINT_PINNED"]) is True
    assert bool(g["AER_RRTM_SW_V25_HISTORICAL_FTP_DISTRIBUTION_PATH_PINNED"]) is True
    assert bool(g["RRTM_SW_V25_INDEPENDENT_EXTRACTED_DISTRIBUTION_FOOTPRINT_QUALIFIED"]) is True
    assert bool(g["AER_RRTM_SW_V25_ARCHIVE_ACQUISITION_VERIFIER_READY"]) is True
    assert bool(g["RRTM_SW_V25_OFFICIAL_DOWNLOAD_AND_EXTRACTED_FOOTPRINT_QUALIFIED"]) is True
    assert bool(g["AER_OFFICIAL_RRTM_SW_V25_ARCHIVE_BYTES_RECOVERED"]) is False
    assert bool(g["AER_OFFICIAL_RRTM_SW_V25_ARCHIVE_HASH_RECOVERED"]) is False
    assert bool(g["RRTM_SW_PREAVERAGING_GENERATOR_RECOVERED"]) is False
    assert bool(g["EXACT_FU96_BAND_WEIGHTING_AVAILABLE"]) is False
    assert bool(g["PRODUCTION_ICE_OPTICS_READY"]) is False
    p = fu96_rrtmg_band_weighting_provenance_contract_payload()
    assert p["contract_version"] == "FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_17"
    assert p["step_version"] == "R5.7.41.3.4.10.30.17"
    assert p["qualification_state"] == EXPECTED_STATE
    assert p["sources"]["aer_rrtm_sw_v25_source_archive_url"] == OFFICIAL_URL


def test_step3q12_local_archive_verifier_hashes_and_manifests_without_self_qualifying(tmp_path: Path):
    archive = tmp_path / "aer_rrtm_sw_v2.5.tar.gz"
    names = [
        "rrtm_sw/src/cldprop.f",
        "rrtm_sw/src/taumoldis.f",
        "rrtm_sw/makefiles/make_rrtm_sw_linux_pgi",
        "rrtm_sw/rrtm_sw_instructions",
        "rrtm_sw/update_rrtm_sw_v2.5.txt",
    ]
    with tarfile.open(archive, "w:gz") as tf:
        for name in names:
            data = (name + "\n").encode()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    r = inspect_archive(archive, source_url=OFFICIAL_URL)
    assert r["archive_bytes_observed"] is True
    assert r["expected_footprint_complete"] is True
    assert r["file_member_count"] == 5
    assert len(r["sha256"]) == 64
    assert len(r["md5"]) == 32
    assert r["provenance_qualified_original_archive_hash"] is False
    assert r["original_tarball_byte_identity_proven"] is False
