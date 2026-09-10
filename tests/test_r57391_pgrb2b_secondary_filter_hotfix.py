from datetime import datetime, timezone

from firecloud.providers.gfs_canvas_optical_probe import build_nomads_request


def test_pgrb2b_uses_secondary_parameter_filter_endpoint_not_primary_filter():
    url, params = build_nomads_request(
        datetime(2026, 9, 10, 6, tzinfo=timezone.utc),
        3,
        (119.164, 120.850, 23.900, 24.779),
    )
    assert url.endswith("/filter_gfs_0p25b.pl")
    assert not url.endswith("/filter_gfs_0p25.pl")
    assert params["file"] == "gfs.t06z.pgrb2b.0p25.f003"
    assert params["dir"] == "/gfs.20260910/06/atmos"
    assert params["var_CLWMR"] == "on"
    assert params["var_ICMR"] == "on"
    assert params["lev_125_mb"] == "on"
