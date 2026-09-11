from firecloud.scenic_spots import (
    DEFAULT_SITE_ID, REGISTRY_VERSION, event_is_compatible, filter_scenic_spots,
    load_scenic_spots, match_scenic_spot, scenic_regions, scenic_spot_by_id,
)


def test_registry_complete_and_unique():
    rows = load_scenic_spots()
    assert REGISTRY_VERSION == "TAIWAN_DAWN_DUSK_SCENIC_SPOTS_V2.2_187"
    assert len(rows) == 187
    assert len({r["site_id"] for r in rows}) == 187
    assert len({r["site_name"] for r in rows}) == 187
    assert all(-90 <= float(r["latitude"]) <= 90 for r in rows)
    assert all(-180 <= float(r["longitude"]) <= 180 for r in rows)


def test_gaomei_is_stable_default_site():
    spot = scenic_spot_by_id(DEFAULT_SITE_ID)
    assert spot is not None
    assert spot["site_name"] == "高美濕地"
    assert abs(spot["latitude"] - 24.311902) < 1e-9
    assert abs(spot["longitude"] - 120.549789) < 1e-9
    assert spot["site_region"] == "中部"
    assert event_is_compatible(spot, "sunset")
    assert not event_is_compatible(spot, "sunrise")


def test_coordinate_match_and_regions():
    matched = match_scenic_spot(24.311902, 120.549789)
    assert matched and matched["site_id"] == DEFAULT_SITE_ID
    assert scenic_regions() == ("北部", "中部", "南部", "花東", "離島")


def test_event_filter_does_not_mutate_registry():
    all_central = filter_scenic_spots(region="中部", event="sunrise", compatible_only=False)
    sunrise_central = filter_scenic_spots(region="中部", event="sunrise", compatible_only=True)
    assert len(all_central) >= len(sunrise_central) > 0
    assert all("sunrise" in r["event_tokens"] for r in sunrise_central)
    assert len(load_scenic_spots()) == 187
