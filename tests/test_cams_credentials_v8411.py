import os
from pathlib import Path
from unittest.mock import patch

from firecloud.providers import cams_native


def test_ads_env_credentials_are_detected_without_cdsapirc(tmp_path):
    with patch.object(Path, "home", return_value=tmp_path), patch.dict(os.environ, {"ADS_API_KEY": "token-test"}, clear=True):
        assert cams_native.credentials_configured() is True
        assert cams_native.credential_source() == "ADS_ENV"
        url, key, source = cams_native._credential_env()
        assert url == "https://ads.atmosphere.copernicus.eu/api"
        assert key == "token-test"
        assert source == "ADS_ENV"


def test_cdsapi_env_can_target_ads_endpoint(tmp_path):
    env = {"CDSAPI_KEY": "token-test", "CDSAPI_URL": "https://ads.atmosphere.copernicus.eu/api"}
    with patch.object(Path, "home", return_value=tmp_path), patch.dict(os.environ, env, clear=True):
        url, key, source = cams_native._credential_env()
        assert url.endswith("/api")
        assert key == "token-test"
        assert source == "CDSAPI_ENV"


def test_provider_status_never_exposes_secret(tmp_path):
    with patch.object(Path, "home", return_value=tmp_path), patch.dict(os.environ, {"ADS_API_KEY": "super-secret"}, clear=True):
        status = cams_native.native_ozone_provider_status()
        assert status["credentials_configured"] is True
        assert status["credential_source"] == "ADS_ENV"
        assert "super-secret" not in str(status)
