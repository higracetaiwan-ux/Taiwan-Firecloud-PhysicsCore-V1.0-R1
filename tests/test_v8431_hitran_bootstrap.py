from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_runtime_version_bumped():
    ns = {}
    exec((ROOT / "firecloud" / "__init__.py").read_text(encoding="utf-8"), ns)
    assert ns["PROGRAM_NAME"] == "Taiwan Firecloud PhysicsCore V1.0"
    assert ns["__version__"].startswith("1.0.0-R5.")


def test_deploy_includes_official_hapi2_pypi_package():
    req = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "hitran-api2==0.2.2" in req
    builder_req = (ROOT / "requirements-hitran-builder.txt").read_text(encoding="utf-8")
    assert "hitran-api2==0.2.2" in builder_req
    assert "github.com/hitranonline/hapi2" not in builder_req


def test_streamlit_has_one_click_hitran_bootstrap_without_key_on_command_line():
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "Legacy：自動下載 line data 並建立 LUT" in app
    assert "可能回 HTTP 404" in app
    assert "bootstrap_hitran_local_db.py" in app
    assert "build_hitran_band_coefficients.py" in app
    # Secret is bridged through environment; it must never be appended as a CLI argument.
    assert '"--api-key"' not in app
